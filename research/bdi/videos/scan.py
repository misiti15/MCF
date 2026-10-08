"""Score the pre-declared video-digest grid (NOTES.md section 0) on train and valid. Educational only - not financial advice.

Frame: setup-lab train/valid joined with research/bdi/videos/data/parts (build.py). First qualifying bar per symbol-day.
Lab geometries: lab r minus the production haircut (2 x 1 bps x price + 0.02) / R. Structural exits: build.py outcomes.
Writes data/all_results.parquet (every scored config), results.csv (L0 + every config positive on both splits with
valid n >= 30), counts.json, plateau.csv, finalists.json."""
import itertools
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.dataset as ds

from mcf.research.setup_lab import load

sys.path.insert(0, str(Path(__file__).parent))
from vid_rules import ANCH, BASE, EXITS, GEOMS, LAYERS, LBASE, VARS, layer, trig  # noqa: E402

HERE = Path(__file__).parent
DATA = HERE / "data"
LAB = ["symbol", "date", "tod", "close", "rsi5", "buyPressure", "gap", "vwapDistPct", "volumeRatio", "dist_pdh_atr",
       "dist_pdl_atr", "atr_d"] + [f"r_{s}_{g}" for s in ("long", "short") for g in ("t1s1", "t05s1", "t1s05")]
WIN = {"am": (950, 1130), "pm": (1130, 1500), "all": (950, 1500)}
TRAIN_END = pd.Timestamp("2026-08-25").date()


def frame():
    keys = ["symbol", "date", "tod"]
    t = ds.dataset(str(DATA / "parts"), format="parquet").to_table()
    t = t.sort_by([("symbol", "ascending"), ("date", "ascending"), ("tod", "ascending")])
    parts = t.to_pandas()
    del t
    parts["date"] = pd.to_datetime(parts["date"]).dt.date
    lab = pd.concat([load("train", columns=LAB), load("valid", columns=LAB)], ignore_index=True)
    if "--partial" in sys.argv:                       # smoke test on the symbols built so far
        lab = lab[lab.symbol.isin(set(parts.symbol))]
    lab = lab.sort_values(keys).reset_index(drop=True)
    assert len(lab) == len(parts), (len(lab), len(parts))
    for k in keys:
        assert (lab[k].to_numpy() == parts[k].to_numpy()).all(), k
    df = pd.concat([lab, parts.drop(columns=keys)], axis=1)
    del parts
    assert np.allclose(df.close, df.c5, rtol=1e-6)
    return df


def trig_neighbours(fam, v, p):
    """Pre-declared one-step neighbours: list of (v', p')."""
    out = []
    P = lambda **kw: {**p, **kw}
    if fam == "MP":
        for k in (v["kmax"] - 1, v["kmax"] + 1):
            if 1 <= k <= 4:
                out.append(({**v, "kmax": k}, p))
        out += [(v, P(tol=0.0)), (v, P(tol=0.05))]
        if v["vol"] == "light":
            out += [(v, P(vthr=0.75)), (v, P(vthr=1.25))]
    elif fam == "VT":
        out += [(v, P(w=0.4)), (v, P(w=0.6))]
        if v["kind"] == "vr2":
            out += [(v, P(vr=1.5)), (v, P(vr=2.5))]
    elif fam == "JD":
        out += [(v, P(tol=0.0)), (v, P(tol=0.05))]
        if v["trend"] == "strong":
            out += [(v, P(strong=0.7)), (v, P(strong=0.9))]
    elif fam == "VA":
        out += [(v, P(pct=60)), (v, P(pct=80))]
    elif fam == "BLK":
        out += [({**v, "L": 18 - v["L"]}, p), ({**v, "c": 80 - v["c"]}, p), (v, P(e=15)), (v, P(e=40))]
    elif fam == "LVN":
        steps = {0.15: (0.10, 0.20), 0.30: (0.20, 0.40)}[v["a"]]
        out += [(v, P(a=x)) for x in steps] + [(v, P(k=25)), (v, P(k=75))]
    elif fam == "AVR":
        out += [(v, P(d=20)), (v, P(d=50))]
    elif fam == "AVF":
        steps = {2.0: (1.5, 2.5), 2.5: (2.0, 3.0)}[v["k"]]
        out += [(v, P(k=x)) for x in steps]
    return out


LNEI = {"rvol15": (1.25, 2.0), "rvol2": (1.5, 2.5), "rsi5_hi": (65, 75), "rsi5_lo": (25, 35), "flowsell": (-0.15, -0.35),
        "flowbuy": (0.15, 0.35), "gap_with": (0.5, 1.5), "gap_against": (0.5, 1.5), "gapper": (1.5, 3.0), "pdroom": (0.25, 0.75)}
BADPAIR = {frozenset(x) for x in (("vwap_with", "vwap_against"), ("rsi5_hi", "rsi5_lo"), ("flowsell", "flowbuy"),
                                  ("gap_with", "gap_against"), ("rvol15", "rvol2"))}
COMBOS = [()] + [(a,) for a in LAYERS] + [c for c in itertools.combinations(LAYERS, 2) if frozenset(c) not in BADPAIR]


# ------------------------------------------------------------------ scoring
class S:
    def __init__(self, df):
        self.df = df
        self.D = {k: df[k].to_numpy() for k in df.columns if k not in ("symbol", "date")}
        key = df.symbol.astype(str).to_numpy() + "|" + df.date.astype(str).to_numpy()
        self.sid = pd.factorize(key)[0]
        dates = df.date.to_numpy()
        ud = np.array(sorted(set(dates)))
        self.dayid = np.searchsorted(ud, dates)
        self.ud = ud
        self.valid = dates > TRAIN_END
        tr_days = ud[ud <= TRAIN_END]
        self.half_day = np.searchsorted(ud, tr_days[len(tr_days) // 2])
        self.tod = df.tod.to_numpy()
        hair = (2 * df.close.to_numpy() * 1e-4 + 0.02) / (0.25 * df.atr_d.to_numpy())
        self.hair = hair
        self.W = {w: (self.tod >= a) & (self.tod <= b) for w, (a, b) in WIN.items()}
        self.base = {}

    def outcome(self, s, ex, v=None, fam=None, p=None):
        sd = "long" if s > 0 else "short"
        if ex in GEOMS:
            return self.D[f"r_{sd}_{ex}"] - self.hair
        if ex == "avw":
            return self.D[f"x_{sd}_avw_{v['anchor']}"]
        if ex == "blk":
            return self.D[f"x_{sd}_blk_{v['L']}_{v['c']}_{(p or {}).get('e', v['e'])}"]
        return self.D[f"x_{sd}_{ex}"]

    def baseline(self, s, ex, v, w, valid):
        bkey = (s, "t1s05" if ex == "blk" else ex, v["anchor"] if ex == "avw" else None, w, valid)
        if bkey not in self.base:
            r = self.outcome(s, "t1s05" if ex == "blk" else ex, v)
            m = self.W[w] & np.isfinite(r) & (self.valid == valid)
            self.base[bkey] = float(r[m].mean())
        return self.base[bkey]

    def stats(self, idx, r):
        if len(idx) == 0:
            return None
        keep = np.r_[True, self.sid[idx][1:] != self.sid[idx][:-1]]
        idx, r = idx[keep], r[keep]
        out = {}
        for nm, msk in (("tr", ~self.valid[idx]), ("va", self.valid[idx])):
            rr, dd = r[msk], self.dayid[idx][msk]
            n = len(rr)
            if n < 2:
                out[nm] = {"n": n}
                continue
            mu = rr.mean()
            sums = np.bincount(dd, weights=rr, minlength=len(self.ud))
            cnts = np.bincount(dd, minlength=len(self.ud))
            used = cnts > 0
            se = np.sqrt(((sums[used] - cnts[used] * mu) ** 2).sum()) / n
            best = np.argmax(np.where(used, sums, -np.inf))
            kb = dd != best
            o = {"n": n, "days": int(used.sum()), "exp": mu, "t": mu / se if se > 0 else 0.0,
                 "exbest": rr[kb].mean() if kb.any() else np.nan, "green": float((sums[used] > 0).mean())}
            if nm == "tr":
                h1, h2 = rr[dd < self.half_day], rr[dd >= self.half_day]
                o["h1"] = h1.mean() if len(h1) else np.nan
                o["h2"] = h2.mean() if len(h2) else np.nan
            out[nm] = o
        return out


def run():
    df = frame()
    sc = S(df)
    D = sc.D
    rows, counts = [], {"declared": 0, "unscored_train_n_lt_60": 0, "scored": 0}
    cache_layers = {}
    for fam, vs in VARS.items():
        for v in vs:
            for s in (1, -1):
                for ex in EXITS[fam]:
                    p = dict(BASE[fam])
                    tm = trig(D, fam, s, v, p, ex)
                    r = sc.outcome(s, ex, v, fam, p)
                    rows_t = np.flatnonzero(tm & np.isfinite(r))
                    rt = r[rows_t]
                    if (s, "L") not in cache_layers:
                        cache_layers[(s, "L")] = {nm: np.asarray(layer(D, nm, s), bool) for nm in LAYERS}
                    LM = cache_layers[(s, "L")]
                    sub = {nm: LM[nm][rows_t] for nm in LAYERS}
                    wsub = {w: sc.W[w][rows_t] for w in WIN}
                    tr_mask = ~sc.valid[rows_t]
                    for combo in COMBOS:
                        mc = np.ones(len(rows_t), bool)
                        for nm in combo:
                            mc &= sub[nm]
                        for w in WIN:
                            counts["declared"] += 1
                            m = mc & wsub[w]
                            if (m & tr_mask).sum() < 60:
                                counts["unscored_train_n_lt_60"] += 1
                                continue
                            st = sc.stats(rows_t[m], rt[m])
                            if st is None or st["tr"].get("n", 0) < 60:
                                counts["unscored_train_n_lt_60"] += 1
                                continue
                            counts["scored"] += 1
                            a, b = st["tr"], st.get("va", {"n": 0})
                            ba, bb = sc.baseline(s, ex, v, w, False), sc.baseline(s, ex, v, w, True)
                            rows.append({"fam": fam, "var": json.dumps(v, sort_keys=True), "side": "long" if s > 0 else "short",
                                         "exit": ex, "layers": "+".join(combo) or "-", "nlay": len(combo), "window": w,
                                         "tr_n": a["n"], "tr_days": a["days"], "tr_exp": a["exp"], "tr_t": a["t"],
                                         "tr_exbest": a["exbest"], "tr_h1": a["h1"], "tr_h2": a["h2"], "tr_base": ba,
                                         "tr_edge": a["exp"] - ba, "va_n": b.get("n", 0), "va_days": b.get("days", 0),
                                         "va_exp": b.get("exp", np.nan), "va_t": b.get("t", np.nan),
                                         "va_exbest": b.get("exbest", np.nan), "va_green": b.get("green", np.nan),
                                         "va_base": bb, "va_edge": b.get("exp", np.nan) - bb})
                    print(fam, v, s, ex, len(rows_t), counts["declared"], flush=True)
    R = pd.DataFrame(rows)
    R.to_parquet(DATA / "all_results.parquet", index=False)
    json.dump(counts, open(HERE / "counts.json", "w"), indent=1)
    return sc, R, counts


def gates_pre(R):
    return ((R.tr_exp > 0) & (R.va_exp > 0) & (R.va_n >= 30) & (R.va_t >= 1.5) & (R.tr_h1 > 0) & (R.tr_h2 > 0)
            & (R.tr_edge > 0) & (R.va_edge > 0))


def score_config(sc, fam, v, p, s, ex, combo, w, lth=None):
    D = sc.D
    m = np.asarray(trig(D, fam, s, v, p, ex), bool) & sc.W[w]
    for nm in combo:
        m &= np.asarray(layer(D, nm, s, (lth or {}).get(nm)), bool)
    r = sc.outcome(s, ex, v, fam, p)
    m &= np.isfinite(r)
    i = np.flatnonzero(m)
    return sc.stats(i, r[i])


def plateau(sc, row):
    fam, v, s, ex, w = row["fam"], json.loads(row["var"]), (1 if row["side"] == "long" else -1), row["exit"], row["window"]
    for k in ("kmax", "L", "c", "e"):
        if k in v:
            v[k] = int(v[k])
    for k in ("a", "k"):
        if k in v:
            v[k] = float(v[k])
    combo = tuple(x for x in row["layers"].split("+") if x != "-")
    p = dict(BASE[fam])
    neigh = [(v2, p2, combo, w, None, f"trig:{json.dumps(v2, sort_keys=True)}|{json.dumps(p2, sort_keys=True)}")
             for v2, p2 in trig_neighbours(fam, v, p)]
    for nm in combo:
        for th in LNEI.get(nm, ()):
            neigh.append((v, p, combo, w, {nm: th}, f"layer:{nm}={th}"))
    for w2 in ({"am": ["all"], "pm": ["all"], "all": ["am", "pm"]}[w]):
        neigh.append((v, p, combo, w2, None, f"window:{w2}"))
    out = []
    for v2, p2, cb, w2, lth, tag in neigh:
        st = score_config(sc, fam, v2, p2, s, ex, cb, w2, lth)
        a = (st or {}).get("tr", {"n": 0})
        b = (st or {}).get("va", {"n": 0})
        out.append({"tag": tag, "tr_n": a.get("n", 0), "tr_exp": a.get("exp", np.nan), "va_n": b.get("n", 0),
                    "va_exp": b.get("exp", np.nan), "va_t": b.get("t", np.nan)})
    P = pd.DataFrame(out)
    ok = P[(P.tr_n >= 10) & (P.va_n >= 10)]
    good = (len(ok) > 0 and ok.tr_exp.mean() > 0 and ok.va_exp.mean() > 0 and (ok.va_exp > 0).mean() >= 2 / 3)
    return P, bool(good)


if __name__ == "__main__":
    sc, R, counts = run()
    pre = R[gates_pre(R)].copy()
    print("pre-plateau passers", len(pre))
    plats, flags = [], []
    for _, row in pre.iterrows():
        P, good = plateau(sc, row)
        P["cfg"] = f"{row['fam']}|{row['var']}|{row['side']}|{row['exit']}|{row['layers']}|{row['window']}"
        plats.append(P)
        flags.append(good)
    pre["plateau_ok"] = flags
    counts["plateau_neighbours"] = int(sum(len(x) for x in plats))
    counts["pre_plateau_passers"] = int(len(pre))
    counts["final_passers"] = int(pre.plateau_ok.sum())
    counts["total_tried"] = counts["declared"] + counts["plateau_neighbours"]
    json.dump(counts, open(HERE / "counts.json", "w"), indent=1)
    (pd.concat(plats) if plats else pd.DataFrame()).to_csv(HERE / "plateau.csv", index=False)
    pre.to_csv(HERE / "passers.csv", index=False)
    print(counts)
