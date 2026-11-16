import sys, importlib, pandas as pd, numpy as np
import sim_low
def mk_path(df):
    mn = df.index.hour * 60 + df.index.minute
    return (np.asarray(mn), df.open.values, df.high.values, df.low.values, df.close.values)
import sim2
SPY = sim2.spy_table("spy1m.parquet")
RF = pd.read_parquet("replay_frames.parquet"); RF["tod"] = RF["tod"].astype(int); RF["date"] = RF.date.astype(str)
RF = RF.merge(SPY, on=["date", "tod"], how="left")
R1 = pd.read_parquet("replay_1min.parquet"); RP = {k: mk_path(g) for k, g in R1.groupby(["symbol", "date"])}
cfgs = getattr(importlib.import_module(sys.argv[1]), sys.argv[2])
for n, v in cfgs.items():
    t = sim_low.book(sim_low.trades(RF, v, lambda s, d: RP.get((s, d))), v); s = sim_low.stats(t)
    print(f"{n:55s} n{s['trades']:4d} avg{s['avg']:+.3f} wo{s['avg_wo_best']:+.3f} wd{s['worst_day']:+.1f} tot{s['total']:+.1f}", flush=True)
