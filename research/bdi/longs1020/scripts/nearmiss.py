"""Detail for the best near-misses: per-half-year, best-day share, overlap with parent. Educational only."""
import json
import numpy as np, pandas as pd
from common import HERE, SCR, split_of
from mcf.research import gates
T = pd.read_parquet(SCR / "b_trades.parquet"); T["date"] = pd.to_datetime(T["date"]).dt.date
out = {}
for base, ex, parent in (("B5-NS1-BRDUP", "t05s1", "B5-NS1-parent"), ("B5-ST2-BRDUP", "t05s1", "B5-ST2-parent"),
                         ("B5-ST2-IDXTURN", "t05s1", "B5-ST2-parent")):
    g = T[T.base == base][["date", "symbol", "tod", "r_" + ex]].rename(columns={"r_" + ex: "r"})
    p = T[T.base == parent][["date", "symbol"]]
    h = pd.PeriodIndex(pd.to_datetime(g.date), freq="Q").astype(str)
    day = g.groupby("date")["r"].sum()
    out[base] = dict(per_quarter={k: [int(len(x)), round(float(x.r.mean()), 3)] for k, x in g.groupby(h)},
                     best_day=str(day.idxmax()), best_day_share=round(float(day.max() / day[day > 0].sum()), 3),
                     share_of_trades_in_parent=round(float(g.merge(p, on=["date", "symbol"]).shape[0] / len(g)), 3),
                     median_tod=int(g.tod.median()), summary=gates.summary(g))
A = pd.read_csv(HERE / "trades_A.csv.gz"); g = A[A.cfg == "A-QQQ-abs015-brd-t05s1"]
h = pd.PeriodIndex(pd.to_datetime(g.date), freq="Q").astype(str)
out["A-QQQ-abs015-brd-t05s1"] = dict(per_quarter={k: [int(len(x)), round(float(x.r.mean()), 3)] for k, x in g.groupby(h)},
                                     median_tod=int(g.tod.median()), summary=gates.summary(g[["date", "r"]].assign(date=lambda z: pd.to_datetime(z.date).dt.date)))
json.dump(out, open(HERE / "nearmiss.json", "w"), indent=1, default=str); print(json.dumps(out, indent=1, default=str))
