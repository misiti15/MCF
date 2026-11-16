import pickle, numpy as np, pandas as pd
import sim2
LOCK = ("2024-11-01", "2025-02-28")
split = lambda d: "TRAIN" if d <= "2025-12-31" else ("VALID" if d <= "2026-10-05" else "FWD")
def mk_path(df):
    mn = df.index.hour * 60 + df.index.minute
    return (np.asarray(mn), df.open.values, df.high.values, df.low.values, df.close.values)
SPY = sim2.spy_table("spy1m.parquet")
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
P2 = pickle.load(open("paths2y.pkl", "rb"))
getB = lambda s, d: P2.get((s, d))
DAYS = {"replay": sorted(set(RF.date)), "2y": sorted(set(pd.read_parquet("spy1m.parquet").index.tz_convert("America/New_York").strftime("%Y-%m-%d")) - set(d for d in [] )) }
DAYS["2y"] = [d for d in DAYS["2y"] if "2024-10-01" <= d <= "2026-11-04" and not (LOCK[0] <= d <= LOCK[1])]
def run(v):
    out = {}
    for test, cand, get in (("replay", RF, getA), ("2y", C, getB)):
        t = sim2.book(sim2.trades(cand, v, get), v)
        if len(t) and test == "2y":
            t["split"] = t.date.map(split)
        out[test] = t
    return out
