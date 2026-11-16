"""2-year candidate rows for L3-gap-slope-rsi5hi-FD (loose superset of every variant: gap <= -2.0, slope > 0.40, RSI(5) > 60),
lab frames, open months only (locked block never read). Educational only - not financial advice."""
import os, sys, pandas as pd
assert not os.environ.get("MCF_HIST_ALLOW_LOCKED")
sys.path.insert(0, "/home/user/MCF/research/history2y"); import lib
cols = ["symbol", "date", "tod", "close", "gap", "fromOpen", "sma20_slope_pct", "atr_d", "adv20", "vwapDistPct", "rsi5", "rsi",
        "atrPct", "upper_wick", "dist_hod_atr", "volumeRatio", "sma20_dist_pct", "pricePosition", "high", "low"]
out = []
for m in lib.months():
    if m in lib.LOCKED_MONTHS: continue
    f = lib.load_month(m, columns=cols)
    f = f[(f.gap <= -2.0) & (f.sma20_slope_pct > 0.40) & (f.rsi5 > 60) & (f.atr_d > 0)]
    out.append(f); print(m, len(f), flush=True)
c = pd.concat(out, ignore_index=True); c["date"] = c.date.astype(str)
assert not c.date.between("2024-11-01", "2025-02-28").any()
c.to_parquet("cand2y.parquet"); print(len(c), c.symbol.nunique(), c.date.min(), c.date.max())
