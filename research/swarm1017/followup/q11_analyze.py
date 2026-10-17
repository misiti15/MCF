"""Q11 analysis: variant minus baseline on the same 1-minute paths (PLAN.md Q11).
    python research/swarm1017/followup/q11_analyze.py SIM.parquet
Educational only - not financial advice."""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
from mcf.research import gates  # noqa: E402
from research.history2y import lib  # noqa: E402

X = pd.read_parquet(sys.argv[1])
X["date"] = pd.to_datetime(X["date"]).dt.date
X = X[np.isfinite(X.r_base)].reset_index(drop=True)          # trades with a 1-minute path
X["train"] = pd.to_datetime(X.date) < "2026-01-01"
REG = lib.regimes()["regime"]
X["regime"] = X.date.map(REG)
s = np.where(X.side.eq("long"), 1.0, -1.0) * X.spy_fo.to_numpy(float)
X["dclass"] = np.where(s > 0.25, "with", np.where(s < -0.25, "against", "flat"))

# parity: 1-minute baseline vs the frames' 5-minute lab outcome (same costs)
par = X.groupby("setup").apply(lambda g: pd.Series({"n": len(g), "frame_exp": g.r.mean(), "m1_exp": g.r_base.mean(),
                                                    "corr": np.corrcoef(g.r, g.r_base)[0, 1] if len(g) > 2 else np.nan}))
rows = []


def score(item, key, sel, rv):
    b = X.r_base[sel].to_numpy(float)
    v = np.asarray(rv, float)[sel.to_numpy()] if not isinstance(rv, pd.Series) else rv[sel].to_numpy(float)
    d = X.date[sel]
    tr = X.train[sel].to_numpy()
    reg = X.regime[sel].to_numpy()
    diff = gates.summary(pd.DataFrame({"date": d, "r": v - b}))
    var = gates.summary(pd.DataFrame({"date": d, "r": v}))
    rows.append({"item": item, "key": key, "n": int(sel.sum()), "exp_base": b.mean(), "exp_var": v.mean(), "t_var": var.get("t"),
                 "d_all": diff.get("exp_r"), "t_diff": diff.get("t"), "d_train": (v - b)[tr].mean(), "d_valid": (v - b)[~tr].mean(),
                 "var_up": v[reg == "up"].mean(), "var_flat": v[reg == "flat"].mean(), "var_down": v[reg == "down"].mean(),
                 "d_up": (v - b)[reg == "up"].mean(), "d_down": (v - b)[reg == "down"].mean()})


# (a) breakeven, MF1-5 parent + FD
mf = X.family.eq("MF")
for v in ("be025", "be05", "be075"):
    for st in sorted(X.setup[mf].unique()):
        score("a", f"{st}|{v}", X.setup.eq(st), X[f"r_{v}"])
    score("a", f"MF-pooled|{v}", mf, X[f"r_{v}"])
# (b) trailing, CWT12 / CWT14 longs
cb = X.setup.str.startswith(("CWT12", "CWT14")) & X.side.eq("long")
for v in ("b0_tgt_tr1a1", "b1_tr05a05", "b2_tr05a1", "b3_tr1a05", "b4_tr1a1"):
    for st in sorted(X.setup[cb].unique()):
        score("b", f"{st}|{v}", X.setup.eq(st), X[f"r_{v}"])
    score("b", f"CWT12+14L-pooled|{v}", cb, X[f"r_{v}"])
# (c) 0.5R stop in one decision-time day class
for fam in ("MF", "NS", "RW", "ST", "L3", "CWT"):
    f = X.family.eq(fam)
    for k in ("with", "against", "flat", "all"):
        rv = X.r_s05.where(X.dclass.eq(k), X.r_base) if k != "all" else X.r_s05
        score("c", f"{fam}|s05_{k}", f, rv)
R = pd.DataFrame(rows)
N = len(R)
BAR = gates.t_required(N)
R["pass"] = (R.d_train > 0) & (R.d_valid > 0) & (R.t_diff.fillna(0) >= BAR)
R.to_csv(HERE / "q11_results.csv", index=False, float_format="%.4f")
par.to_csv(HERE / "q11_parity.csv", float_format="%.4f")
summ = {"configs": N, "bar": BAR, "n_trades_with_path": int(len(X)), "passes": R[R["pass"]][["item", "key", "d_all", "t_diff", "d_train", "d_valid", "exp_var"]].to_dict("records"),
        "class_share": X.groupby("family").dclass.value_counts(normalize=True).round(3).unstack().to_dict("index")}
(HERE / "q11_summary.json").write_text(json.dumps(summ, indent=1, default=float))
pd.set_option("display.width", 250)
print("N", N, "bar", BAR)
print(par.round(3).to_string())
print(R.round(3).to_string())
