"""TT1 (Team G definition) on live SPY 1-min bars for 10-06..11-24; checked against G/gate.parquet where they overlap."""
import numpy as np, pandas as pd
P = "/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/pyramid/"
b = pd.read_parquet(P + "L3/live_SPY.parquet"); b.index = pd.DatetimeIndex(b.index).tz_convert("America/New_York")
hm = b.index.hour * 100 + b.index.minute; b = b[(hm >= 930) & (hm < 1600)].copy(); b["date"] = b.index.date.astype(str)
out = []
for dt, g in b.groupby("date"):
    m = (g.index.hour * 60 + g.index.minute).to_numpy(); c = g.close.to_numpy(); v = g.volume.to_numpy()
    vw = np.cumsum(c * v) / np.cumsum(v); dev = c / vw - 1
    below = (dev <= -0.0005) & (m >= 575)
    cb = np.cumsum(below)
    for T in range(9 * 60 + 36, 16 * 60):
        i = np.searchsorted(m, T) - 1
        if i < 0: continue
        j = np.searchsorted(m, T - 30) - 1   # bar labelled <= T-31
        rec = c[i] > vw[i]; wb = cb[i] > 0; up = (j >= 0) and c[i] / c[j] - 1 > 0
        out.append((dt, (T // 60) * 100 + T % 60, rec and wb and up, rec and up))
L = pd.DataFrame(out, columns=["date", "T", "TT1", "TT0"]); L.to_parquet(P + "R3B/tt1_live.parquet")
G = pd.read_parquet(P + "G/gate.parquet"); G = G[G.src == "live"][["date", "T", "TT1"]]
x = L.merge(G, on=["date", "T"], suffixes=("", "_g")); print(len(x), (x.TT1 == x.TT1_g).mean(), L.date.nunique())
