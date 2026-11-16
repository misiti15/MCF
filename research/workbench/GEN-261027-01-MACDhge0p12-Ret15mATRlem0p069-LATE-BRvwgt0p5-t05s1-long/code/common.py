"""Mechanic GEN-261027-01 (Late Pullback Buy, MACD rising): shared constants. Educational only - not financial advice."""
import sys
WT = "/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/wt-wb-gen27101"
sys.path.insert(0, WT); sys.path.insert(0, "/home/user/MCF/research/history2y")
OUT = "/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/mech-gen27101/"
IND = ["macd_hist", "ret3_atr", "ret3", "ret6", "ret12", "rsi5", "rsi7", "vwap_atr", "day_pos", "fromOpen_atr", "from_pc_atr",
       "atr_d_pct", "adx7", "di_diff7", "rvol_day", "z12", "dist_lod_atr", "dist_hod_atr", "macdPct", "emaDiff", "gap_atr",
       "ret_since950_atr", "flow3", "bars_since_hod", "sma20_slope_pct", "volumeRatio", "day_range_atr", "eff6", "ret1",
       "ema9_slope_atr", "bar_range_atr", "lower_wick"]
LOCK = ("2024-11-01", "2025-02-28")
PRE = dict(lo=1330, hi=1500, adv=10e6, mh=0.04, r3=-0.03)   # candidate prefilter (wider than every variant)
