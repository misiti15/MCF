import pickle, numpy as np, pandas as pd
import sim
LOCK = ("2024-11-01", "2025-02-28")
split = lambda d: "TRAIN" if d <= "2025-12-31" else ("VALID" if d <= "2026-10-05" else "FWD")
def mk_path(df):
    mn = df.index.hour * 60 + df.index.minute
    return (np.asarray(mn), df.open.values, df.high.values, df.low.values, df.close.values)
SPY = sim.spy_table("spy1m.parquet")
RF = pd.read_parquet("replay_frames.parquet"); RF["tod"] = RF["tod"].astype(int); RF["date"] = RF.date.astype(str)
RF = RF.merge(SPY, on=["date", "tod"], how="left")
R1 = pd.read_parquet("replay_1min.parquet")
RP = {k: mk_path(g) for k, g in R1.groupby(["symbol", "date"])}
getA = lambda s, d: RP.get((s, d))
C = pd.read_parquet("cand2y.parquet"); C["tod"] = C.tod.astype(int)
assert not C.date.between(*LOCK).any()
rate = pd.read_parquet("etb_rate.parquet").rate
C = C[C.symbol.map(rate) >= 0.9].reset_index(drop=True)
C = C.merge(SPY, on=["date", "tod"], how="left").sort_values(["symbol", "date", "tod"]).reset_index(drop=True)
import os
RO = bool(os.environ.get("REPLAY_ONLY"))
P2 = {} if RO else pickle.load(open("paths2y.pkl", "rb"))
getB = lambda s, d: P2.get((s, d))
DAYS = {"replay": sorted(set(RF.date)), "2y": sorted(set(C.date))}
def run(v):
    out = {}
    for test, cand, get in (("replay", RF, getA),) + (() if RO else (("2y", C, getB),)):
        t = sim.book(sim.trades(cand, v, get), v)
        if test == "2y" and len(t):
            t["split"] = t.date.map(split)
        out[test] = t
    return out
