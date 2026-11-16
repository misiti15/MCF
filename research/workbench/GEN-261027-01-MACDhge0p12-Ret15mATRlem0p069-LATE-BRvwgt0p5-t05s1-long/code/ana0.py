"""Mechanic GEN-261027-01: quick component analysis of the parent on the 2y frames with the frame lab outcome
(r_long_t05s1; screening only - the decision numbers come from the 1-minute engine). Educational only - not financial advice."""
import pandas as pd, numpy as np
from sim import *
C = pd.read_parquet(OUT + "cand2y.parquet")
t = select(C, dict(PARENT)); t["r"] = t.r_long_t05s1; t["sp"] = np.where(t.date <= "2025-12-31", "T", "V")
print("parent", len(t), t.r.mean().round(4), t.groupby("sp").r.agg(["size", "mean"]).round(4).to_dict())
def tab(col, q=5):
    x = pd.qcut(t[col], q, duplicates="drop")
    g = t.groupby(x, observed=True).agg(n=("r", "size"), avg=("r", "mean"), T=("r", lambda r: r[t.loc[r.index, "sp"] == "T"].mean()),
                                        V=("r", lambda r: r[t.loc[r.index, "sp"] == "V"].mean()))
    print(f"== {col}"); print(g.round(3).to_string())
for c in ["tod", "macd_hist", "ret3_atr", "breadth", "spy950", "br_chg", "ret12", "ret6", "vwap_atr", "day_pos", "fromOpen_atr", "from_pc_atr",
          "atr_d_pct", "adx7", "di_diff7", "rsi5", "rsi7", "z12", "dist_lod_atr", "dist_hod_atr", "macdPct", "emaDiff", "gap_atr",
          "ret_since950_atr", "flow3", "rvol_day", "sma20_slope_pct", "volumeRatio", "day_range_atr", "eff6", "ret1", "close", "adv20",
          "ema9_slope_atr", "bar_range_atr", "lower_wick"]:
    tab(c)
