"""Inputs: session replay (Workbench pack 10-12..11-12 + extension 11-13..11-17) and the 2-year pack (locked block never read)."""
import pickle, numpy as np, pandas as pd
S = "/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad"
LOCK = ("2024-11-01", "2025-02-28")
split = lambda d: "TRAIN" if d <= "2025-12-31" else ("VALID" if d <= "2026-10-05" else "FWD")


def mk_path(df):
    mn = df.index.hour * 60 + df.index.minute
    return (np.asarray(mn), df.open.values, df.high.values, df.low.values, df.close.values)


# SPY 1-min: Workbench cache (to 11-16) + 11-16..11-17 GET
a = pd.read_parquet(f"{S}/upday/spy1m_all.parquet"); a.index = pd.DatetimeIndex(a.index).tz_convert("America/New_York")
b = pd.read_parquet("spy_ext.parquet"); b = b.set_index(pd.DatetimeIndex(b.ts).tz_convert("America/New_York"))[["open", "high", "low", "close"]].astype(float)
SPY1 = pd.concat([a[["open", "high", "low", "close"]], b]); SPY1 = SPY1[~SPY1.index.duplicated(keep="first")].sort_index()
SPY1["date"] = SPY1.index.strftime("%Y-%m-%d"); SPY1["mn"] = SPY1.index.hour * 60 + SPY1.index.minute
rows = []
for d, g in SPY1.groupby("date"):
    g = g.set_index("mn"); r = g.loc[570:959]
    if 570 not in r.index or 599 not in r.index:
        continue
    o = r.open.loc[570]; c10 = r.close.loc[599]; c16 = r.close.iloc[-1]
    rows.append(dict(date=d, spy_o=o, spy10=(c10 / o - 1) * 100, spy_oc=(c16 / o - 1) * 100))
SD = pd.DataFrame(rows).set_index("date")
SD["dtype_oc"] = np.where(SD.spy_oc > 0.25, "up", np.where(SD.spy_oc < -0.25, "down", "quiet"))
SD["start10"] = np.where(SD.spy10 >= 0.25, "strong", np.where(SD.spy10 < 0, "weak", "flat"))

R1 = pd.concat([pd.read_parquet(f"{S}/mech-l3w/replay_1min.parquet"), pd.read_parquet("replay_1min_ext.parquet")])
R1.index = pd.DatetimeIndex(R1.index).tz_convert("America/New_York") if R1.index.tz is not None else R1.index
RP = {k: mk_path(g.sort_index()) for k, g in R1.groupby(["symbol", "date"])}
getA = lambda s, d: RP.get((s, d))
RF = pd.concat([pd.read_parquet(f"{S}/mech-l3w/replay_frames.parquet"), pd.read_parquet("replay_frames_ext.parquet")])
RF["tod"] = RF["tod"].astype(int); RF["date"] = RF.date.astype(str)
RF = RF.reset_index(drop=True)

C = pd.read_parquet("cand2yx.parquet"); C["tod"] = C.tod.astype(int); C["date"] = C.date.astype(str)
assert not C.date.between(*LOCK).any()
rate = pd.read_parquet("etb_rate.parquet").rate
C = C[(C.symbol.map(rate) >= 0.9) & (C.gap <= -2.5)].reset_index(drop=True)
P2 = pickle.load(open("paths2y.pkl", "rb"))
assert not any(LOCK[0] <= d <= LOCK[1] for (_, d) in P2)
getB = lambda s, d: P2.get((s, d))
DAYS = {"replay": sorted(set(RF.date)), "2y": sorted(set(pd.read_parquet("cand2yx.parquet").date.astype(str)))}
TESTS = {"replay": (RF, getA), "2y": (C, getB)}
