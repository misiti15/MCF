"""Stack study step 3: apply the pre-declared live-probation criterion (NOTES.md 1.7) to the scan, with walk-forward,
ex-best-day, plateau neighbours (counted as configurations) and overlap with the live setups; pick diverse candidates.
Writes candidates.json, data/finalists.csv. Educational only - not financial advice."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import scan as S  # noqa: E402
from mcf.research import gates  # noqa: E402

LIVE = ["heat_fade_long", "heat_fade_short", "exhaustion_short", "MF1-945-flowsell-vwapup", "MF2-open-rsimidhi-flowsell",
        "MF3-open-flowsell-rsi5hi", "MF4-h40-open-flowsell", "MF5-flowsell-vwapup-rsi5hi", "NS1-rsidip-rsi5pop-long",
        "NS2-sma50break-overbought-short", "NS3-failed-vwap-reclaim-short", "NS4-pm-vwap-reclaim-oversold-short",
        "NS5-sma50-flush-oversold-long"]
DATES = np.array(pd.to_datetime(S.DATES).date)
LOCKED_M = ["2024-11", "2024-12", "2025-01", "2025-02"]


def trades_of(fam, d, side, w, flist, geom, tp=None):
    G = S.gather(fam, d, None, tp)
    s = 1 if side == "long" else -1
    o = S.quick(G, S.wmask(G, w) & S.fmask(G, s, flist), side, geom)
    if not o["n"]:
        return o, pd.DataFrame(columns=["date", "symbol", "r"])
    idx = o["_idx"]
    t = pd.DataFrame({"date": DATES[G["day"][idx]], "sym": G["sym"][idx], "tod": G["tod"][idx],
                      "r": G[f"p_{side}_{geom}"][idx].astype(float)})
    return o, t


def neighbours(fam, flist):
    """one-step neighbours of each threshold: list of (trigger param, filter list)."""
    out = []
    if fam in S.TRIG_GRID:
        g, p0 = S.TRIG_GRID[fam], S.TRIG_DEFAULT[fam]
        i = g.index(p0)
        out += [(g[j], flist) for j in (i - 1, i + 1) if 0 <= j < len(g)]
    for k, (n, p) in enumerate(flist):
        if n in S.FGRID and p is not None:
            g = S.FGRID[n]
            i = g.index(p)
            for j in (i - 1, i + 1):
                if 0 <= j < len(g):
                    fl = list(flist)
                    fl[k] = (n, g[j])
                    out.append((S.TRIG_DEFAULT.get(fam), fl))
    return out


def main():
    df = pd.read_csv(HERE / "data" / "scan_all.csv")
    n_scan = len(df)
    pre = df[(df.n >= 150) & (df.exp_up > 0) & (df.exp_down > 0) & (df.t >= 2.0)
             & (df.maxday <= 0.10) & ((df.n_flat < 30) | (df.exp_flat > 0))].copy()
    pre["fk"] = pre["filters"].map(lambda x: json.dumps(sorted(json.loads(x))))
    pre = pre.drop_duplicates(["fam", "dir", "side", "win", "fk", "geom"]).sort_values("t", ascending=False)
    print("scan configs", n_scan, "pass cheap gates", len(pre), flush=True)
    sym_names = pd.read_csv(HERE / "data" / "symbols.csv").iloc[:, 0].to_numpy()
    lt = pd.read_parquet(S.ROOT / "research" / "history2y" / "data" / "lab_trades.parquet")
    live_keys = set(zip(lt.loc[lt.setup.isin(LIVE), "symbol"].astype(str), lt.loc[lt.setup.isin(LIVE), "date"].astype(str)))
    rows = []
    n_extra = 0
    for r in pre.head(150).itertuples():
        fl = [tuple(x) for x in json.loads(r.filters)]
        o, t = trades_of(r.fam, r.dir, r.side, r.win, fl, r.geom, S.TRIG_DEFAULT.get(r.fam))
        n_extra += 1
        summ = gates.summary(t)
        wf = gates.walk_forward(t, exclude_months=LOCKED_M)
        nb = []
        for tp, fl2 in neighbours(r.fam, fl):
            o2 = trades_of(r.fam, r.dir, r.side, r.win, fl2, r.geom, tp)[0]
            n_extra += 1
            nb.append(o2.get("exp", np.nan) if o2["n"] else np.nan)
        nbm = float(np.nanmean(nb)) if nb else None
        keys = list(zip(sym_names[t["sym"]].astype(str), t["date"].astype(str)))
        ov_live = float(np.mean([k in live_keys for k in keys]))
        ok = (summ["ex_best_day"] > 0 and (wf["share_positive"] or 0) >= 0.6
              and (nbm is None or (nbm > 0 and np.nanmin(nb) > -0.05)))
        rows.append({"cfg": r.cfg, "fam": r.fam, "dir": r.dir, "side": r.side, "win": r.win, "filters": r.filters,
                     "geom": r.geom, "n": summ["n"], "per_day": round(summ["n"] / 426, 2), "win_rate": summ["win_rate"],
                     "exp": summ["exp_r"], "t": summ["t"], "exp_up": round(r.exp_up, 4), "n_up": r.n_up,
                     "exp_flat": round(r.exp_flat, 4), "n_flat": r.n_flat, "exp_down": round(r.exp_down, 4),
                     "n_down": r.n_down, "wf": wf["share_positive"], "plateau_mean": None if nbm is None else round(nbm, 4),
                     "plateau_min": None if not nb else round(float(np.nanmin(nb)), 4), "n_neigh": len(nb),
                     "ex_best": summ["ex_best_day"], "overlap_live": round(ov_live, 3), "pass": ok,
                     "keys": keys})
        print(r.cfg, summ["n"], summ["exp_r"], summ["t"], wf["share_positive"], nbm, ok, flush=True)
    res = pd.DataFrame(rows)
    counts = json.load(open(HERE / "counts.json"))
    counts["finalist_rescore_and_plateau"] = n_extra
    counts["total"] = counts["configs"] + n_extra
    json.dump(counts, open(HERE / "counts.json", "w"), indent=1)
    treq = gates.t_required(counts["total"])
    # diverse pick
    chosen = []
    for r in res[res["pass"]].sort_values("t", ascending=False).itertuples():
        if any(c.fam == r.fam and c.side == r.side and c.win == r.win for c in chosen):
            continue
        ks = set(r.keys)
        if any(len(ks & set(c.keys)) / max(1, min(len(ks), len(c.keys))) > 0.30 for c in chosen):
            continue
        chosen.append(r)
    res.drop(columns="keys").to_csv(HERE / "finalists.csv", index=False)
    out = []
    for i, c in enumerate(chosen, 1):
        others = [x for x in chosen if x is not c]
        ov = max([len(set(c.keys) & set(x.keys)) / len(c.keys) for x in others], default=0)
        fl = [tuple(x) for x in json.loads(c.filters)]
        tp = S.TRIG_DEFAULT.get(c.fam)
        cid = f"ST{i}-{c.fam}{c.dir}-{c.side}-{c.win}-{c.geom}"
        lo, hi = S.WINDOWS[c.win]
        stats = (f"n {c.n} ({c.per_day}/day), win {c.win_rate}, exp {c.exp:+.3f}R, day-clustered t {c.t}; "
                 f"up {c.exp_up:+.3f} (n {c.n_up}) / flat {c.exp_flat:+.3f} (n {c.n_flat}) / down {c.exp_down:+.3f} (n {c.n_down}); "
                 f"walk-forward + share {c.wf}; plateau mean {c.plateau_mean}; ex-best-day {c.ex_best:+.3f}.")
        layers = [f"trigger {c.fam} {c.dir}" + ("" if tp is None else f" ({tp})")] + \
                 [f"{n}" + ("" if p is None else f" {p}") for n, p in fl] + [f"{lo}-{hi} ET bar close"]
        out.append({"id": cid, "desc": "Basic stack: " + "; ".join(layers) + ".", "side": c.side, "geom": c.geom,
                    "lo": lo, "hi": hi, "stats": stats, "treq": treq, "ntries": counts["total"],
                    "trigger": (c.fam, c.dir, tp), "filters": fl, "layers": layers,
                    "row": {k: getattr(c, k) for k in ["cfg", "n", "per_day", "win_rate", "exp", "t", "exp_up", "n_up",
                                                       "exp_flat", "n_flat", "exp_down", "n_down", "wf", "plateau_mean",
                                                       "plateau_min", "ex_best", "overlap_live"]} | {"overlap_cands": round(ov, 3)}})
    json.dump(out, open(HERE / "candidates.json", "w"), indent=1, default=float)
    print("passers", int(res["pass"].sum()), "chosen", len(chosen), "t_required", treq, "N", counts["total"])


if __name__ == "__main__":
    main()
