"""FIT-only diagnosis of the BEG-03 base (booked FIT trades). Educational only - not financial advice."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

W = Path(sys.argv[1])
t = pd.read_parquet(W / "bk_base_fit.parquet")
t = t[t.half == "fit"].copy()
assert (t.date < "2025-10-01").all()
t["hold"] = t.xm - t.em
t["cost_r"] = t.r_gross - t.r
kn = {0: "time 12:00", 1: "stop/trail", 2: "target"}
print("FIT booked", len(t), "avg R", round(t.r.mean(), 4), "gross", round(t.r_gross.mean(), 4),
      "cost/trade R", round(t.cost_r.mean(), 4), "total", round(t.r.sum(), 1))
print("\nby exit kind\n", t.groupby(t.kind.map(kn)).r.agg(["size", "mean", "sum"]).round(3))
full = (t.kind == 1) & (t.r_gross <= -0.95)
print("\nfull initial-stop losers", int(full.sum()), round(t[full].r.sum(), 1), "| trail stops (r_gross > -0.95)",
      int(((t.kind == 1) & ~full).sum()), round(t[(t.kind == 1) & ~full].r.mean(), 3))
print("\nhold of full-stop losers (min)\n", pd.cut(t[full].hold, [-1, 2, 5, 15, 30, 60, 200]).value_counts().sort_index())
print("\nby entry time\n", t.groupby(pd.cut(t.tod, [949, 959, 1014, 1029, 1059])).r.agg(["size", "mean", "sum"]).round(3))
print("\nby stop %\n", t.groupby(pd.cut(t.stop_pct, [0.39, 0.8, 1.2, 1.8, 3.01])).r.agg(["size", "mean", "sum"]).round(3))
print("\nby gap %\n", t.groupby(pd.cut(t.gap, [3, 5, 8, 12, 20, 200])).r.agg(["size", "mean", "sum"]).round(3))
print("\nby rvol20\n", t.groupby(pd.cut(t.rvol20, [3, 5, 8, 15, 1e9])).r.agg(["size", "mean", "sum"]).round(3))
print("\nby price\n", t.groupby(pd.cut(t.entry, [5, 15, 40, 100, 220])).r.agg(["size", "mean", "sum"]).round(3))
print("\nby cost R\n", t.groupby(pd.cut(t.cost_r, [0, 0.05, 0.1, 0.15, 1])).r.agg(["size", "mean", "sum"]).round(3))
print("\n25 worst losers\n", t.nsmallest(25, "r")[["symbol", "date", "tod", "xt", "kind", "gap", "rvol20", "stop_pct",
                                                   "r_gross", "r"]].round(3).to_string())
