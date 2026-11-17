"""Inputs for the UPDAY bench (same replay / 2-year inputs as the RERUN; SPY 1-min extended to 11-16)."""
import pickle, numpy as np, pandas as pd
import sim, sim3
LOCK = ("2024-11-01", "2025-02-28")
split = lambda d: "TRAIN" if d <= "2025-12-31" else ("VALID" if d <= "2026-10-05" else "FWD")


def mk_path(df):
    mn = df.index.hour * 60 + df.index.minute
    return (np.asarray(mn), df.open.values, df.high.values, df.low.values, df.close.values)


S1 = pd.read_parquet("spy1m_all.parquet"); S1.index = pd.DatetimeIndex(S1.index).tz_convert("America/New_York")
SPY, SPYC = sim3.spy_tables(S1)
DT = pd.read_parquet("spyday.parquet").set_index("date")       # full-day label SPY 09:50 close -> 16:00 (reporting only)


def px950(get, s, d):
    p = get(s, d)
    if p is None:
        return np.nan
    mn, o, h, l, c = p
    i = np.searchsorted(mn, 589)
    return c[i] if i < len(mn) and mn[i] == 589 else np.nan


def prep(c, get):
    c = c.merge(SPY, on=["date", "tod"], how="left")
    keys = c[["symbol", "date"]].drop_duplicates()
    m = {(a, b): px950(get, a, b) for a, b in keys.itertuples(index=False)}
    c["px950"] = [m[(a, b)] for a, b in zip(c.symbol, c.date)]
    c["rs950"] = (c.close / c.px950 - 1) * 100 - c.spy950
    return c.sort_values(["symbol", "date", "tod"]).reset_index(drop=True)


RF = pd.read_parquet("replay_frames.parquet"); RF["tod"] = RF["tod"].astype(int); RF["date"] = RF.date.astype(str)
R1 = pd.read_parquet("replay_1min.parquet")
RP = {k: mk_path(g) for k, g in R1.groupby(["symbol", "date"])}
getA = lambda s, d: RP.get((s, d))
RF = prep(RF, getA)
C = pd.read_parquet("cand2yx.parquet"); C["tod"] = C.tod.astype(int)
assert not C.date.between(*LOCK).any()
rate = pd.read_parquet("etb_rate.parquet").rate
C = C[C.symbol.map(rate) >= 0.9].reset_index(drop=True)
D2 = sorted(set(C.date))
C = C[(C.gap <= -2.5)].drop(columns=["spy_fo"], errors="ignore")   # loose superset of every config (parent gap -2.66)
P2 = pickle.load(open("paths2y.pkl", "rb"))
getB = lambda s, d: P2.get((s, d))
C = prep(C, getB)
DAYS = {"replay": sorted(set(RF.date)), "2y": D2}


def run(v):
    out = {}
    for test, cand, get in (("replay", RF, getA), ("2y", C, getB)):
        t = sim.book(sim3.trades(cand, v, get, SPYC), v)
        t["dtype"] = t.date.map(DT.dtype)
        if test == "2y":
            t["split"] = t.date.map(split)
        out[test] = t
    return out
