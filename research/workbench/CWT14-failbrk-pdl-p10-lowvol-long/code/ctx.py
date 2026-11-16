"""SPY market state per (date, tod = 5-minute bar close) 09:50-15:00, anchored AFTER 09:50 (owner direction rule):
SPY % since the 09:50 close, position in the 09:30-09:50 range, % vs session VWAP. Only 1-minute bars closed by `tod`.
Locked block dropped. Reuses the sibling job's SPY loader. Educational only - not financial advice."""
import sys, numpy as np, pandas as pd
sys.path.insert(0, "/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/wt-wb-cwt14pdl/research/workbench/CWT14-failbrk-orl-p10-long/code2")
OUT = "/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/mech-cwt14pdl/"
TEAMD = ["2026-11-05", "2026-11-06", "2026-11-09", "2026-11-10"]
a = pd.read_parquet("/home/user/MCF/data/cache_hist/1Min/SPY.parquet")[["open", "high", "low", "close", "volume"]]
t = pd.concat([pd.read_parquet(f"/home/user/MCF/data/team/1Min/{d}.parquet") for d in TEAMD]); t = t[t.symbol == "SPY"]
t["ts"] = pd.to_datetime(t.ts).dt.tz_convert("America/New_York")
b = pd.concat([a, t.set_index("ts")[["open", "high", "low", "close", "volume"]]]).sort_index(); b = b[~b.index.duplicated()]
hm = b.index.hour * 100 + b.index.minute; b = b[(hm >= 930) & (hm < 1600)].copy()
b["date"] = b.index.strftime("%Y-%m-%d"); b = b[~((b.date >= "2024-11-01") & (b.date <= "2025-02-28"))]
b["m"] = b.index.hour * 60 + b.index.minute
rows = []
for d, g in b.groupby("date"):
    tp = (g.high + g.low + g.close) / 3; vw = ((tp * g.volume).cumsum() / g.volume.cumsum()).to_numpy()
    m = g.m.to_numpy(); c = g.close.to_numpy()
    early = m < 590
    if not early.any(): continue
    hi, lo, c950 = g.high[early].max(), g.low[early].min(), c[early][-1]
    for tod in range(950, 1505, 5):
        if tod % 100 >= 60: continue
        k = np.searchsorted(m, tod // 100 * 60 + tod % 100) - 1
        if k < 0: continue
        rows.append((d, tod, (c[k] / c950 - 1) * 100, (c[k] - lo) / (hi - lo) if hi > lo else np.nan, (c[k] / vw[k] - 1) * 100))
C = pd.DataFrame(rows, columns=["date", "tod", "spy_d950", "spy_rpos", "spy_vw"])
C.to_parquet(OUT + "ctx.parquet"); print(C.shape, C.date.min(), C.date.max())
