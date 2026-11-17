import pickle, sys, numpy as np, pandas as pd
sys.path.insert(0, "code")
import sim3, band
sys.path.insert(0, "/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/mech-rw5/code")
from sim2 import spy_table
LOCK = ("2024-11-01", "2025-02-28")
split = lambda d: "TRAIN" if d <= "2025-12-31" else ("VALID" if d <= "2026-10-05" else "FWD")
def mk_path(df):
    mn = df.index.hour * 60 + df.index.minute
    return (np.asarray(mn), df.open.values, df.high.values, df.low.values, df.close.values)
SPY = spy_table("spy1m.parquet")
RF = pd.read_parquet("replay_frames.parquet"); RF["tod"] = RF["tod"].astype(int); RF["date"] = RF.date.astype(str)
RF = RF.sort_values(["symbol", "date", "tod"]).reset_index(drop=True)
key = (RF.symbol + "|" + RF.date).values
p = np.r_[np.nan, RF.sma50_dist_pct.values[:-1]]; p[np.r_[True, key[1:] != key[:-1]]] = np.nan; RF["p_sma50"] = p
RF["dist_hod_atr"] = (RF.groupby(["symbol", "date"]).high.cummax() - RF.close) / RF.atr_d   # frame value is NaN in the replay (ATR set after extra_features)
R1 = pd.read_parquet("replay_1min.parquet")
RP, BT = {}, []
for (s, d), g in R1.groupby(["symbol", "date"]):
    g = g.sort_index(); RP[(s, d)] = mk_path(g); BT.append(band.table(g, s, d))
RF = RF.merge(pd.concat(BT), on=["symbol", "date", "tod"], how="left").merge(SPY, on=["date", "tod"], how="left")
getA = lambda s, d: RP.get((s, d))
C = pd.read_parquet("cand2y.parquet"); C["tod"] = C.tod.astype(int)
assert not C.date.between(*LOCK).any()
rate = pd.read_parquet("etb_rate.parquet").rate
C = C[C.symbol.map(rate) >= 0.9].reset_index(drop=True)
C = C.merge(pd.read_parquet("band2y.parquet"), on=["symbol", "date", "tod"], how="left").merge(SPY, on=["date", "tod"], how="left")
C = C.sort_values(["symbol", "date", "tod"]).reset_index(drop=True)
P2 = pickle.load(open("paths2y.pkl", "rb"))
getB = lambda s, d: P2.get((s, d))
DAYS = {"replay": sorted(set(RF.date))}
_sd = sorted(set(SPY.date))
DAYS["2y"] = [d for d in _sd if "2024-10-01" <= d <= "2026-11-04" and not (LOCK[0] <= d <= LOCK[1])]
def run(v):
    out = {}
    for test, cand, get in (("replay", RF, getA), ("2y", C, getB)):
        t = sim3.book(sim3.trades(cand, v, get), v)
        if len(t) and test == "2y":
            t["split"] = t.date.map(split)
        out[test] = t
    return out
