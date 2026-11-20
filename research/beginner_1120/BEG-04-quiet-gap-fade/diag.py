"""FIT-only loser diagnosis of the BEG-04 base (reads WORK/bk_base_all.parquet, FIT rows only).
Educational only - not financial advice."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

W = Path(sys.argv[1])
t = pd.read_parquet(W / "bk_base_all.parquet")
t = t[(t.test == "t1") & (t.half == "fit")].copy()
print("FIT booked", len(t), "avg R", round(t.r.mean(), 4), "gross", round(t.r_gross.mean(), 4))


def tab(by, name):
    g = t.groupby(by, observed=True).r.agg(["size", "mean", "sum"]).round(3)
    print(f"\n-- {name}\n{g}")


t["exit"] = t.kind.map({0: "time", 1: "stop", 2: "target"})
tab("exit", "exit kind")
tab("side", "side (-1 short after gap up, +1 long after gap down)")
tab(pd.cut(t.sig_tod, [949, 1014, 1044, 1114, 1200]), "decision time")
tab(pd.cut(t.gap.abs(), [1.5, 2.5, 3.5, 6.01]), "|gap|")
tab(pd.cut(t.stop_atr, [0, 0.15, 0.25, 0.3499, 0.36]), "stop / ATR (0.35 = capped)")
tab("r20_capped", "R20 stop capped by 0.35 ATR")
tab(pd.cut(t.tgt_r_plan, [1.2, 1.6, 2.5, 4, 1e9]), "planned target distance in R")
tab(pd.cut(t.rvol20, [0, 0.7, 1.0, 1.5]), "RVOL20")
tab("spy", "SPY day type") if "spy" in t else None
t["hold"] = t.xm - t.em
st = t[t.kind == 1]
print("\nstop-outs:", len(st), "median hold", st.hold.median(), "| within 10 min", int((st.hold <= 10).sum()))
print("\nworst 25 losers")
print(t.nsmallest(25, "r")[["symbol", "date", "side", "sig_tod", "gap", "stop_atr", "tgt_r_plan", "exit", "hold",
                             "r"]].round(3).to_string())
# MFE proxy unavailable here; time-exit outcomes
tm = t[t.kind == 0]
print("\ntime exits:", len(tm), "avg R", round(tm.r.mean(), 3), "share > 0", round((tm.r > 0).mean(), 3))
