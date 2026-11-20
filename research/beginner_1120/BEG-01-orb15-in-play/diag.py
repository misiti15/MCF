"""FIT-only diagnosis of BEG-01 base (booked trades, testing rules). Educational only - not financial advice.
python diag.py WORK"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

W = Path(sys.argv[1])
t = pd.read_parquet(W / "booked_t1_base_fit.parquet")
assert (t.half == "fit").all()
print("FIT booked", len(t), "avgR", round(t.r.mean(), 4), "gross", round(t.r_gross.mean(), 4))
t["cost_r"] = t.r_gross - t.r
t["kindn"] = t.kind.map({0: "time", 1: "stop", 2: "target"})
t.loc[(t.kind == 1) & t.be, "kindn"] = "be-stop"
t["stop_pct"] = t.risk / t.entry * 100
t["hold"] = t.xm - t.em


def tab(col, bins=None):
    x = pd.cut(t[col], bins) if bins is not None else t[col]
    g = t.groupby(x, observed=True).agg(n=("r", "size"), avg_r=("r", "mean"), gross=("r_gross", "mean"),
                                        cost=("cost_r", "mean"), sum_r=("r", "sum"))
    print(f"\n-- by {col}\n", g.round(3).to_string())


tab("kindn")
tab("side")
tab("chase")
tab("ehm", [949, 959, 1014, 1029, 1059, 1130])
tab("stop_pct", [0, 0.3, 0.45, 0.6, 1, 10])
tab("cost_r", [0, 0.1, 0.15, 0.2, 0.3, 1])
tab("rank", [0, 5, 10, 15, 20])
tab("rvol", [0, 3, 5, 8, 15, 1e9])
tab("atr", [0, 2, 4, 8, 1e9])
w = t.nsmallest(max(20, len(t) // 10), "r")
print("\n-- worst decile losers:", len(w), "sum R", round(w.r.sum(), 1), "of total", round(t.r.sum(), 1))
print(w.kindn.value_counts().to_dict(), "chase share", round(w.chase.mean(), 2),
      "median hold min", float(w.hold.median()), "later reached target", round(w.later_tgt.mean(), 2))
print("stops:", int((t.kindn == "stop").sum()), "stopped then later reached the 2R target:",
      round(t.loc[t.kindn == "stop", "later_tgt"].mean(), 3),
      "stopped within 5 min:", round((t.loc[t.kindn == "stop", "hold"] <= 5).mean(), 3))
print("mfe>=1R share", round((t.mfe >= 1).mean(), 3), "mfe>=2R", round((t.mfe >= 2).mean(), 3))
print("loss R quantiles", t.r.quantile([0.01, 0.05, 0.1, 0.5]).round(2).to_dict())
