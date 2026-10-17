"""arena-index-etf search, stages 0-2 on TRAIN (see PLAN.md). Every scored configuration goes to results_stage.csv.
Usage: python search.py <rows_dir> <out_dir>. Educational only - not financial advice."""
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from common import FILTER_INDS, GEOMS, LIVE, SCREEN, SIDES, WINDOWS  # noqa: E402
from engine import Panel, Sub, cond_mat, first_trades, stats_split, train_gate  # noqa: E402

from mcf.research.arena.indicators import INDICATORS  # noqa: E402

ROWS, OUT = sys.argv[1], Path(sys.argv[2])
OUT.mkdir(parents=True, exist_ok=True)
t0 = time.time()
P = Panel(ROWS)
T = Sub(P, P.sd_split == 0)
print("loaded", P.nsd, T.nsd, f"{time.time()-t0:.0f}s", flush=True)
A = P.A
trainrows = (pd.to_datetime(A["date"]).dt.strftime("%Y-%m") <= "2025-12").to_numpy()


def qs(name):
    x = A.loc[trainrows, name].to_numpy(float)
    x = x[np.isfinite(x)]
    return {q: float(np.quantile(x, q)) for q in (0.05, 0.2, 0.5, 0.8, 0.95)}, x


def bins(name):
    ind = INDICATORS[name]
    q, x = qs(name)
    if ind.kind == "binary":
        return [(name, "==", 1.0), (name, "==", 0.0)]
    if ind.kind == "cat" or len(np.unique(x)) <= 12 and ind.kind != "cont":
        return [(name, "==", float(v)) for v in np.unique(x)]
    out = [(name, "<=", q[0.05]), (name, "<=", q[0.2]), (name, "<=", q[0.5]), (name, ">=", q[0.5]),
           (name, ">=", q[0.8]), (name, ">=", q[0.95])]
    seen, res = set(), []
    for c in out:
        if (c[1], c[2]) not in seen:
            seen.add((c[1], c[2]))
            res.append(c)
    return res


def filt_bins(name):
    q, _ = qs(name)
    return [(name, "<=", q[0.2]), (name, "<=", q[0.5]), (name, ">=", q[0.5]), (name, ">=", q[0.8])]


cache = {}
WM = {w: T.win_mask(w)[None, :] for w in WINDOWS}
rows = []
count = {"stage0": 0, "stage1": 0, "stage2": 0}


def score(conds, side, geom, w, stage):
    M = WM[w]
    for c in conds:
        M = M & cond_mat(T, cache, c)
    sd, k, r, c, e = first_trades(T, M, f"{side}_{geom}")
    s = stats_split(T, sd, r, c, e, 0)
    count[stage] += 1
    row = {"stage": stage, "conds": json.dumps([[a, b, v] for a, b, v in conds]), "side": side, "geom": geom,
           "window": f"{w[0]}-{w[1]}", **{f"tr_{k_}": v for k_, v in s.items()}}
    row["gate_train"] = bool(s["n"] and train_gate(s))
    rows.append(row)
    return row


# ---- stage 0: singles
allbins = {n: bins(n) for n in LIVE}
for n, bl in allbins.items():
    for c in bl:
        for w in WINDOWS:
            for g in GEOMS:
                for s in SIDES:
                    score([c], s, g, w, "stage0")
    for k in [k for k in cache if k[0] == n or (k[0] == "__ind" and k[1] == n)]:
        del cache[k]
print("stage0", count["stage0"], f"{time.time()-t0:.0f}s", flush=True)
R0 = pd.DataFrame(rows)
R0["ind"] = R0.conds.map(lambda s: json.loads(s)[0][0])

# ---- triggers per side
scr = pd.read_parquet(SCREEN)
trig = {}
for s in SIDES:
    x = R0[(R0.side == s) & (R0.tr_n >= 300)].sort_values("tr_exc_e", ascending=False)
    x = x.drop_duplicates("conds").drop_duplicates("ind").head(20)
    tl = [tuple(json.loads(c)[0]) for c in x.conds]
    used = set(x.ind)
    y = scr[(scr.side == s) & scr.live & (scr.n >= 2000)].sort_values("excess", ascending=False)
    y = y[~y.indicator.isin(used)].drop_duplicates("indicator").head(10)
    for r in y.itertuples():
        tl.append((r.indicator, "between", (float(r.lo), float(r.hi))) if r.op == "between" else (r.indicator, r.op, float(r.lo)))
    trig[s] = [(a, b, v if not isinstance(v, list) else tuple(v)) for a, b, v in tl]
filters = [c for n in FILTER_INDS for c in filt_bins(n)]
json.dump({"triggers": {s: [list(map(str, t)) for t in v] for s, v in trig.items()},
           "filters": [list(map(str, f)) for f in filters]}, open(OUT / "space.json", "w"), indent=1)
print("triggers", {s: len(v) for s, v in trig.items()}, "filters", len(filters), flush=True)

# ---- stage 1: pairs
for s in SIDES:
    for tc in trig[s]:
        for fc in filters:
            if fc[0] == tc[0]:
                continue
            for w in WINDOWS:
                for g in GEOMS:
                    score([tc, fc], s, g, w, "stage1")
    print("stage1", s, count["stage1"], f"{time.time()-t0:.0f}s", flush=True)

# ---- stage 2: triples
R = pd.DataFrame(rows)
for s in SIDES:
    x = R[(R.stage == "stage1") & (R.side == s) & (R.tr_n >= 150)].sort_values("tr_t", ascending=False).head(150)
    for r in x.itertuples():
        cs = [tuple(c) if not isinstance(c[2], list) else (c[0], c[1], tuple(c[2])) for c in json.loads(r.conds)]
        w = tuple(int(v) for v in r.window.split("-"))
        for fc in filters:
            if fc[0] in (cs[0][0], cs[1][0]):
                continue
            score(cs + [fc], s, r.geom, w, "stage2")
    print("stage2", s, count["stage2"], f"{time.time()-t0:.0f}s", flush=True)

R = pd.DataFrame(rows)
R.to_csv(OUT / "results_train.csv", index=False)
json.dump(count, open(OUT / "count_stages.json", "w"))
print("done", count, int(R.gate_train.sum()), f"{time.time()-t0:.0f}s", flush=True)
