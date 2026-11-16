"""RW6G1 2-year candidate rows (loose superset of every variant: SMA50 cross-up bar, fromOpen > 1.5, RSI(14) >= 50,
ADV >= $40M) from the lab frames, open months only (locked never read)."""
import os, sys, numpy as np, pandas as pd
assert not os.environ.get("MCF_HIST_ALLOW_LOCKED")
sys.path.insert(0, "/home/user/MCF/research/history2y"); import lib
cols = ["symbol", "date", "tod", "close", "high", "low", "gap", "fromOpen", "rsi", "rsi5", "heat", "buyPressure", "atr_d", "adv20",
        "vwapDistPct", "atrPct", "upper_wick", "dist_hod_atr", "dist_lod_atr", "volumeRatio", "sma20_dist_pct", "sma50_dist_pct",
        "sma20_slope_pct", "pricePosition", "flow3", "rsiSlope", "momentum", "dist_pdh_atr"]
out = []
for m in lib.months():
    if m in lib.LOCKED_MONTHS: continue
    f = lib.load_month(m, columns=cols)
    key = (f.symbol.astype(str) + "|" + f.date.astype(str)).values
    p = np.r_[np.nan, f.sma50_dist_pct.values[:-1]]; p[np.r_[True, key[1:] != key[:-1]]] = np.nan
    f["p_sma50"] = p
    f = f[(f.sma50_dist_pct > 0) & (f.p_sma50 <= 0) & (f.fromOpen > 1.5) & (f.rsi >= 50) & (f.adv20 >= 40e6) & (f.atr_d > 0) & (f.tod >= 935)]
    try:
        cx = lib.load_context(m); f = f.merge(cx[["date", "tod", "spy_fo", "breadth"]], on=["date", "tod"], how="left")
    except Exception as e:
        print("ctx", m, e)
    out.append(f); print(m, len(f), flush=True)
c = pd.concat(out, ignore_index=True); c["date"] = c.date.astype(str)
assert not c.date.between("2024-11-01", "2025-02-28").any()
c.to_parquet("cand2y.parquet"); print(len(c), c.symbol.nunique(), c.date.min(), c.date.max())
