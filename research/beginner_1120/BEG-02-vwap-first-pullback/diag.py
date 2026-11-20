"""FIT-only diagnosis of the BEG-02 base (which part loses: entry timing, stop, target, window, filter).
Educational only - not financial advice."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

W = Path(sys.argv[1])
t = pd.read_parquet(W / "bk_base_t1.parquet")
t = t[t.half == "fit"].copy()
print("FIT booked", len(t), "avg R", round(t.r.mean(), 4), "gross", round(t.r_gross.mean(), 4))
kind = {0: "time/maxhold", 1: "stop", 2: "target"}
t["exit"] = t.kind.map(kind)
t["hold"] = t.xm - t.em
t["timestop"] = (t.kind == 0) & (t.hold <= 62)


def tab(col, bins=None):
    x = pd.cut(t[col], bins) if bins is not None else t[col]
    g = t.groupby(x, observed=True).r.agg(["size", "mean", "sum"]).round(3)
    print("--", col)
    print(g.to_string())


tab("exit")
tab("timestop")
tab("side")
tab("sig_tod", [949, 1000, 1030, 1100, 1200, 1300])
tab("stop_atr", [0, 0.15001, 0.2, 0.3, 0.5, 5])
tab("tgt_r", [1.49, 1.75, 1.99, 2.01])
tab("move950", [-50, -5, -3, -2, 2, 3, 5, 50])
tab("rank", [0, 10, 20, 30, 50])
tab("hold", [-1, 5, 15, 30, 60, 90, 121])
w = t.nsmallest(25, "r")
print("-- worst 25 FIT")
print(w[["symbol", "date", "side", "sig_tod", "tod", "entry", "stop", "risk", "stop_atr", "tgt_r", "exit", "hold", "r",
         "move950", "rank"]].to_string(index=False))
day = t.groupby("date").r.sum().sort_values()
print("-- worst FIT days", day.head(8).round(2).to_dict())
print("costs: avg gross - net", round((t.r_gross - t.r).mean(), 4), "stop_cost_r median", round(t.stop_cost_r.median(), 3))
