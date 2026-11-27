"""R3N stage 1: draw N=300 rules (seeded), score on FIT only (lab basis), select finalists. PREREG.md.
Educational only - not financial advice."""
import json, sys, time
import numpy as np, pandas as pd
from common import *  # noqa
import research.history2y.lib as lib

lib.DATA = B.DATA
FIT = ["2024-10"] + [f"2025-{m:02d}" for m in range(3, 10)]
for m in FIT:
    assert m not in B.LOCKED_MONTHS
NS = 170


def draw():
    rng = np.random.default_rng(20261125)
    out, seen = [], set()
    for side, n, TR, CX in (("long", 240, TRIG_L, CTX_L), ("short", 60, TRIG_S, CTX_S)):
        k_ = 0
        while k_ < n:
            t = TR[rng.integers(len(TR))]
            k = rng.choice([0, 1, 2], p=[0.15, 0.45, 0.40])
            cx = sorted(rng.choice(CX, size=k, replace=False).tolist()) if k else []
            if k == 2 and family(cx[0]) == family(cx[1]):
                continue
            g = GEOMS[rng.integers(3)]; w = list(WINS)[rng.integers(3)]
            key = (side, t, tuple(cx), g, w)
            if key in seen:
                continue
            seen.add(key); out.append(dict(side=side, trig=t, ctx=cx, geom=g, win=w)); k_ += 1
    return out


COLS = ["symbol", "date", "tod", "close", "high", "low", "atr_d", "adv20", "vwapDistPct", "volumeRatio", "volumeSurge",
        "upper_wick", "lower_wick", "dist_hod_atr", "dist_lod_atr", "dist_pdh_atr", "dist_pdl_atr", "dist_round_atr",
        "fromOpen", "gap", "rsi", "rsi5", "macdPct", "flow3", "flow9prev", "bull_div", "bear_div", "pricePosition",
        "sma20_dist_pct", "sma20_slope_pct", "heat", "buyPressure"] + \
       [f"{a}_{s}_{g}" for a in ("r", "win") for s in ("long", "short") for g in GEOMS]


def build(months):
    parts, sd0 = [], 0
    for mo in months:
        t0 = time.time()
        df = lib.load_month(mo, columns=COLS, context=True)
        df = df[np.nan_to_num(df.adv20.to_numpy(float)) >= ADV].reset_index(drop=True)
        df["symbol"] = df.symbol.astype(str); df["date"] = df.date.astype(str)
        B.no_locked(df.date.unique())
        df = ensure_cols(df)
        P = prims(df)
        tod = df.tod.to_numpy(int)
        bits = np.zeros(len(df), np.uint64)
        for p in ALLP:
            bits[P[p]] |= BIT[p]
        ok = {s: base_ok(df, s) for s in ("long", "short")}
        key = df.symbol.to_numpy() + "|" + df.date.to_numpy()
        sd = np.cumsum(np.r_[True, key[1:] != key[:-1]]) + sd0; sd0 = sd.max() + 1
        keep = (tod >= 1000) & (tod <= 1500)
        d = dict(bits=bits[keep], sd=sd[keep], tod=tod[keep], date=df.date.to_numpy()[keep],
                 okl=ok["long"][keep], oks=ok["short"][keep])
        for s in ("long", "short"):
            for g in GEOMS:
                d[f"{s}_{g}"] = lab_r(df, s, g)[keep].astype(np.float32)
        parts.append(d)
        print(mo, len(df), int(keep.sum()), f"{time.time()-t0:.0f}s", flush=True)
        del df, P
    return {k: np.concatenate([p[k] for p in parts]) for k in parts[0]}


def first_idx(D, r):
    need = np.uint64(0)
    for c in [r["trig"]] + r["ctx"]:
        need |= BIT[c]
    a, b = WINS[r["win"]]
    rr = D[f"{r['side']}_{r['geom']}"]
    m = ((D["bits"] & need) == need) & (D["tod"] >= a) & (D["tod"] <= b) & np.isfinite(rr)
    m &= D["okl"] if r["side"] == "long" else D["oks"]
    ii = np.flatnonzero(m)
    if not len(ii):
        return ii
    s = D["sd"][ii]
    return ii[np.r_[True, s[1:] != s[:-1]]]


def fitness(D, ii, r, spy):
    x = pd.DataFrame({"date": D["date"][ii], "r": D[f"{r['side']}_{r['geom']}"][ii].astype(float)})
    n = len(x); o = dict(n=n, ps=n / NS)
    if n < 3:
        return o | dict(elig=False, F=np.nan)
    day = x.groupby("date").r.sum(); tot = day.sum(); best = day.idxmax()
    o["avg"] = x.r.mean(); o["wo"] = x.r[x.date != best].mean(); o["share"] = day.max() / tot if tot > 0 else np.nan
    ty = x.date.map(spy); o["n_dn"] = int((ty == "down").sum()); o["dn"] = x.r[ty == "down"].mean() if o["n_dn"] else np.nan
    o["up"] = x.r[ty == "up"].mean(); o["flat"] = x.r[ty == "flat"].mean()
    e = (x.r - x.r.mean()).groupby(x.date).sum(); se = np.sqrt((e ** 2).sum()) / n
    o["t"] = x.r.mean() / se if se > 0 else np.nan
    o["elig"] = bool(n >= 85 and n / NS <= 25 and o["n_dn"] >= 20 and tot > 0 and o["share"] < 0.5)
    o["F"] = min(o["avg"], o["wo"], o["dn"]) if o["n_dn"] else np.nan
    return o


def main():
    rules = draw()
    json.dump(rules, open("rules.json", "w"))
    spy = B.spy_t1()
    D = build(FIT)
    assert len(set(D["date"])) == NS, len(set(D["date"]))
    rows, sets = [], {}
    for i, r in enumerate(rules):
        ii = first_idx(D, r)
        f = fitness(D, ii, r, spy)
        rows.append(dict(id=i, name=rule_name(r), **{k: r[k] for k in ("side", "trig", "geom", "win")},
                         ctx="+".join(r["ctx"]), **f))
        sets[i] = set(D["sd"][ii].tolist())
    C = pd.DataFrame(rows)
    C.to_csv("candidates_fit.csv", index=False)
    pick = []
    for side, k in (("long", 3), ("short", 2)):
        z = C[(C.side == side) & C.elig].sort_values("F", ascending=False)
        kept = []
        for _, q in z.iterrows():
            if len(kept) == k:
                break
            if any(q.trig == C.loc[j, "trig"] for j in kept):
                continue
            if any(len(sets[q.id] & sets[j]) / max(len(sets[q.id] | sets[j]), 1) >= 0.30 for j in kept):
                continue
            kept.append(q.id)
        pick += [dict(id=int(j), rule=rules[j], name=C.loc[j, "name"], F=float(C.loc[j, "F"]),
                      filler=bool(C.loc[j, "F"] <= 0)) for j in kept]
    json.dump(pick, open("picks.json", "w"), indent=1)
    pd.set_option("display.width", 250)
    print("eligible:", C.groupby("side").elig.sum().to_dict(), "F>0:", C[C.elig & (C.F > 0)].groupby("side").size().to_dict())
    print(C[C.elig].sort_values("F", ascending=False).groupby("side").head(10)[
        ["id", "name", "n", "ps", "avg", "wo", "dn", "up", "share", "t", "F"]].round(3).to_string(index=False))
    for p in pick:
        print("PICK", p["name"], round(p["F"], 4), "filler" if p["filler"] else "")


if __name__ == "__main__":
    main()
