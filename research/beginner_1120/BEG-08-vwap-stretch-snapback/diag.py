"""BEG-08 FIT-only diagnosis of the base (reads WORK/bk_base_fit.parquet only). python diag.py WORK
Educational only - not financial advice."""
import sys
from pathlib import Path

import pandas as pd

W = Path(sys.argv[1])
t = pd.read_parquet(W / "bk_base_fit.parquet")
assert set(t.half) == {"fit"}
day = t.groupby("date").r.agg(["sum", "count"]).sort_values("sum")
w5 = day.index[:5]
print(day.head(5).round(1), day.tail(3).round(1), sep="\n")
print("w/o 5 worst days avg R", round(t[~t.date.isin(w5)].r.mean(), 3))
print(t.groupby("kind").r.agg(["count", "mean", "sum"]).round(3))
print(t.groupby("side").r.agg(["count", "mean", "sum"]).round(3))
for col, bins in (("sig_tod", [959, 1029, 1100, 1200, 1300, 1430]), ("stop_atr", [0, .1, .15, .2, .3, .5, 5]),
                  ("tgt_r_plan", [0, 1.5, 2, 3, 5, 100]), ("stretch_atr", [-10, -1.5, -1, -.8, .8, 1, 1.5, 10]),
                  ("run_len", [0, 1, 3, 10, 30, 400]), ("rank_rvol20", [30, 60, 100, 200, 400, 2000])):
    x = t.assign(b=pd.cut(t[col], bins))
    y = x.groupby("b", observed=True).r.agg(["count", "mean", "sum"])
    y["wo_worst5"] = [x[(x.b == b) & ~x.date.isin(w5)].r.mean() for b in y.index]
    print(col, y.round(3), sep="\n")
print(t.nsmallest(30, "r")[["symbol", "date", "side", "sig_tod", "stop_atr", "tgt_r_plan", "kind", "r", "run_len"]])
