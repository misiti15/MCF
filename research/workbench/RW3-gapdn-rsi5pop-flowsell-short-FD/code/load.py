"""Shared loader: (A) live-session replay frames + 1-min paths, (B) 2-year candidates (E90 borrow proxy, ADV >= $95M) + paths.
Educational only - not financial advice."""
import pickle, numpy as np, pandas as pd
import sim_rw3 as sim
LOCK = ("2024-11-01", "2025-02-28")
split = lambda d: "TRAIN" if d <= "2025-12-31" else ("VALID" if d <= "2026-10-05" else "FWD")
def mk_path(df):
    mn = df.index.hour * 60 + df.index.minute
    return (np.asarray(mn), df.open.values, df.high.values, df.low.values, df.close.values)
SPY = sim.spy_table("spy1m.parquet")
RF = pd.read_parquet("replay_frames.parquet"); RF["tod"] = RF["tod"].astype(int); RF["date"] = RF.date.astype(str)
RF = RF[RF.date <= "2026-11-13"].merge(SPY, on=["date", "tod"], how="left")
_dv = pd.read_parquet("/home/user/MCF/research/history2y/data/daily.parquet", columns=["symbol", "date", "adv20"])
_dv = _dv[_dv.date.astype(str) >= "2026-09-01"]; _dv["date"] = _dv.date.astype(str)
_k = RF[["symbol", "date"]].drop_duplicates()
_k["adv20"] = [(_dv[(_dv.symbol == s) & (_dv.date < d)].adv20.iloc[-1] if ((_dv.symbol == s) & (_dv.date < d)).any() else float("nan")) for s, d in zip(_k.symbol, _k.date)]
RF = RF.merge(_k, on=["symbol", "date"], how="left")
R1 = pd.read_parquet("replay_1min.parquet")
RP = {k: mk_path(g) for k, g in R1.groupby(["symbol", "date"])}
getA = lambda s, d: RP.get((s, d))
C = pd.read_parquet("cand2y.parquet"); C["tod"] = C.tod.astype(int)
assert not C.date.between(*LOCK).any()
rate = pd.read_parquet("etb_rate.parquet").rate
C = C[(C.symbol.map(rate) >= 0.9) & (C.adv20 >= 95e6)].reset_index(drop=True)
C = C.merge(SPY, on=["date", "tod"], how="left").sort_values(["symbol", "date", "tod"]).reset_index(drop=True)
P2 = pickle.load(open("paths2y.pkl", "rb"))
getB = lambda s, d: P2.get((s, d))
DAYS = {"replay": sorted(set(RF.date)), "2y": sorted(set(C.date))}
def run(v, tests=("replay", "2y")):
    out = {}
    for test, cand, get in (("replay", RF, getA), ("2y", C, getB)):
        if test not in tests: continue
        t = sim.book(sim.trades(cand, v, get), v)
        if len(t): t["split"] = t.date.map(split) if test == "2y" else None
        out[test] = t
    return out
