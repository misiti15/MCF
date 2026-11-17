"""Mechanic GEN-261023-09 (Late Failed-Breakdown Pop Short): shared constants. Educational only - not financial advice."""
import sys
WT = "/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/wt-wb-gen23109"
sys.path.insert(0, WT); sys.path.insert(0, "/home/user/MCF/research/history2y")
OUT = "/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/mech-gen23109/"
SETUP = "GEN-261023-09-ORBfailDn-Ret15mge0p54-LATE-BRvwgt0p7-holdtr-short"
IND = ["orb_fail_dn", "ret3", "ret1", "ret6", "ret12", "rsi5", "rsi7", "vwap_atr", "day_pos", "fromOpen_atr", "from_pc_atr",
       "atr_d_pct", "adx7", "di_diff7", "rvol_day", "z12", "dist_hod_atr", "dist_lod_atr", "gap_atr", "ret_since950_atr",
       "flow3", "bars_since_hod", "bars_since_lod", "volumeRatio", "day_range_atr", "eff6", "upper_wick", "bar_range_atr",
       "macd_hist", "sma20_dist_pct", "emaDiff", "or_low_dist_atr", "or_high_dist_atr", "dist_pdh_atr", "ret3_atr",
       "vwap_cross_n", "bb_pctb12"]
LOCK = ("2024-11-01", "2025-02-28")
# loose candidate box (the parent and every variant select inside it): breadth NOT filtered
BOX = dict(lo=1330, hi=1500, adv=75e6, r3=0.30)
END2Y = "2026-10-22"     # 2-year backtest ends before the live window (Gen from 2026-10-23)
