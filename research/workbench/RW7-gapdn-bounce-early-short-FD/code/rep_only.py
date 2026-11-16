import sys, os; sys.path.insert(0, "code")
import pandas as pd, numpy as np, sim2, importlib
def mk_path(df):
    mn = df.index.hour * 60 + df.index.minute
    return (np.asarray(mn), df.open.values, df.high.values, df.low.values, df.close.values)
SPY = sim2.spy_table("spy1m.parquet")
RF = pd.read_parquet("replay_frames.parquet"); RF["tod"] = RF["tod"].astype(int); RF["date"] = RF.date.astype(str)
RF = RF.merge(SPY, on=["date", "tod"], how="left")
RP = {k: mk_path(g) for k, g in pd.read_parquet("replay_1min.parquet").groupby(["symbol", "date"])}
cf = getattr(importlib.import_module(sys.argv[1]), sys.argv[2])
days = sorted(set(RF.date)); base = None
for n, v in cf.items():
    t = sim2.book(sim2.trades(RF, v, lambda s, d: RP.get((s, d))), v)
    if n == "PARENT": base = t
    s = sim2.stats(t); tt, dr = sim2.paired_t(base, t, days)
    print(f"{n:62s} n{s['trades']:4d} avg{s['avg']:+.3f} wo{s['avg_wo_best']:+.3f} wd{s['worst_day']:+6.1f} tot{s['total']:+6.1f} t{tt:+.2f}", flush=True)
