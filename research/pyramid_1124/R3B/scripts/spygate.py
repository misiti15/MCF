"""SPYOPEN gate per (date, T): SPY last 1-min close in bars labelled [09:30, T) >= 09:30 open. T1 cache_hist (locked
filtered), T2 cache_fresh, live Alpaca SIP (L3/live_SPY.parquet). Educational only - not financial advice."""
import numpy as np, pandas as pd, pyarrow.dataset as pads
TZ = "America/New_York"; LOCK = ("2024-11-01", "2025-02-28")
P = "/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/pyramid/"
def hist():
    f = pads.field("__index_level_0__")
    b = pads.dataset("/home/user/MCF/data/cache_hist/1Min/SPY.parquet", format="parquet").to_table(
        filter=(f < pd.Timestamp(LOCK[0], tz=TZ)) | (f >= pd.Timestamp("2025-03-01", tz=TZ))).to_pandas()
    if "__index_level_0__" in b.columns: b = b.set_index("__index_level_0__")
    return b
def fresh():
    return pd.read_parquet("/home/user/MCF/data/cache_fresh/1Min/SPY.parquet")
def live():
    return pd.read_parquet(P + "L3/live_SPY.parquet")
out = []
for src, b in (("T1", hist()), ("T2", fresh()), ("LIVE", live())):
    b.index = pd.DatetimeIndex(b.index).tz_convert(TZ); b = b.sort_index()
    hm = b.index.hour * 100 + b.index.minute
    b = b[(hm >= 930) & (hm < 1600)]
    b["date"] = b.index.date.astype(str)
    d = pd.Series(b.date.unique()); assert not ((d >= LOCK[0]) & (d <= LOCK[1])).any()
    for dt, g in b.groupby("date"):
        if g.index[0].hour * 100 + g.index[0].minute != 930: continue
        o = g.open.iloc[0]
        m = (g.index.hour * 60 + g.index.minute).to_numpy()
        c = g.close.to_numpy()
        Ts = np.arange(9 * 60 + 36, 16 * 60)
        idx = np.searchsorted(m, Ts, side="left") - 1   # last bar labelled < T
        ok = idx >= 0
        out.append(pd.DataFrame({"date": dt, "T": (Ts[ok] // 60) * 100 + Ts[ok] % 60, "spyopen": c[idx[ok]] >= o,
                                 "spy_vs_open": c[idx[ok]] / o - 1, "src": src}))
G = pd.concat(out, ignore_index=True)
G.to_parquet(P + "R3B/spyopen.parquet"); print(G.groupby("src").date.nunique(), G.spyopen.mean())
