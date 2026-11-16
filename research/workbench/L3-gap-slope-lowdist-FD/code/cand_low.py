"""2-year candidate rows for L3-gap-slope-lowdist-FD (loose superset of every variant), open months only (locked never read)."""
import os, sys, pandas as pd
assert not os.environ.get("MCF_HIST_ALLOW_LOCKED")
sys.path.insert(0, "/home/user/MCF/research/history2y"); import lib
cols = ["symbol", "date", "tod", "close", "gap", "fromOpen", "sma20_slope_pct", "atr_d", "adv20", "dist_lod_atr", "vwapDistPct",
        "rsi5", "rsi", "atrPct", "upper_wick", "dist_hod_atr", "dist_pdl_atr", "volumeRatio", "sma20_dist_pct", "pricePosition",
        "high", "low", "flow3"]
out = []
for m in lib.months():
    if m in lib.LOCKED_MONTHS: continue
    f = lib.load_month(m, columns=cols)
    f = f[(f.gap <= -2.0) & (f.sma20_slope_pct > 0.2) & (f.dist_lod_atr > 0.5) & (f.dist_lod_atr <= 1.3) & (f.atr_d > 0)]
    try:
        cx = lib.load_context(m); f = f.merge(cx[["date", "tod", "spy_fo", "breadth"]], on=["date", "tod"], how="left")
    except Exception as e:
        print("ctx", m, e)
    out.append(f); print(m, len(f), flush=True)
c = pd.concat(out, ignore_index=True); c["date"] = c.date.astype(str)
assert not c.date.between("2024-11-01", "2025-02-28").any()
c.to_parquet("cand_low.parquet"); print(len(c), c.symbol.nunique(), c.date.min(), c.date.max())
