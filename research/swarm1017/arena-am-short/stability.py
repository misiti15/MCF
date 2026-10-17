"""arena-am-short stability check of the three near-misses (PLAN.md addendum). Educational only - not financial advice.
python research/swarm1017/arena-am-short/stability.py <scratch rows dir>"""
import itertools
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.argv = sys.argv[:2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
import search as S  # noqa: E402
from mcf.research.arena.combine import cond_mask, evaluate_combo  # noqa: E402

HERE = Path(__file__).resolve().parent
SEEDS = {
    "N1": [("sma20_slope_pct", "<=", -0.7373), ("day_vs_prev_range", "<=", 0.4091), ("buyPressure", ">=", 0.3115)],
    "N2": [("vwapDistPct", ">=", 0.9177), ("day_vs_prev_range", "<=", 0.4091), ("di_diff7", "<=", 0.0)],
    "N3": [("rv12", ">=", 0.6005), ("day_vs_prev_range", "<=", 0.4091), ("from_pc_atr", "<=", -0.3489)],
}
W = (1000, 1100)
names = sorted({c[0] for v in SEEDS.values() for c in v})
cols = ["symbol", "date", "tod"] + [f"{p}_short_{g}" for p in ("r", "c") for g in S.GEOMS] + names
A = S.load_rows(cols)
tr = S.Fast(A, (A["split"] == "train").to_numpy())
va = S.Fast(A, (A["split"] == "valid").to_numpy())
trw = (A["split"] == "train").to_numpy() & (A["tod"].to_numpy() >= W[0]) & (A["tod"].to_numpy() < W[1])
rows, n_conf = [], 0
for sid, conds in SEEDS.items():
    opts = []
    for nm, op, v in conds:
        x = A.loc[trw, nm].to_numpy(float)
        x = x[np.isfinite(x)]
        p = (x <= v).mean()
        opts.append([(nm, op, float(np.quantile(x, min(max(p + d, 0.01), 0.99)))) for d in (-0.1, 0.0, 0.1)])
    for cs in itertools.product(*opts):
        mtr = np.ones(len(tr.sel), bool)
        mva = np.ones(len(va.sel), bool)
        for c in cs:
            m = cond_mask(A, c)
            mtr &= m[tr.sel]
            mva &= m[va.sel]
        for g in S.GEOMS:
            a = tr.stats(mtr & tr.win(W), g)
            b = va.stats(mva & va.win(W), g)
            n_conf += 1
            rows.append({"seed": sid, "geom": g, "key": S.key(list(cs)), **{f"tr_{k}": v for k, v in a.items()},
                         **{f"va_{k}": v for k, v in b.items()}})
R = pd.DataFrame(rows)
R.to_csv(HERE / "stability.csv", index=False, float_format="%.5g")
summ = {}
for (sid, g), x in R.groupby(["seed", "geom"]):
    summ[f"{sid}_{g}"] = {"n_sets": len(x), "share_train_pos": round(float((x.tr_exp > 0).mean()), 3),
                          "share_valid_pos": round(float((x.va_exp > 0).mean()), 3),
                          "share_both_pos": round(float(((x.tr_exp > 0) & (x.va_exp > 0)).mean()), 3),
                          "median_tr_exp": round(float(x.tr_exp.median()), 4), "median_va_exp": round(float(x.va_exp.median()), 4),
                          "median_tr_n": float(x.tr_n.median())}
json.dump({"configs_scored": n_conf, "summary": summ}, open(HERE / "stability.json", "w"), indent=1)
print(json.dumps(summ, indent=1), "configs", n_conf)
