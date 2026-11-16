"""Mechanic GEN-261026-03 (Lunch New-Low Short): shared constants. Educational only - not financial advice."""
import sys
WT = "/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/wt-wb-gen26103"
sys.path.insert(0, WT)
OUT = "/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/mech-gen26103/"
SETUP = "GEN-261026-03-NewLOD-Flow3lem0p37-FromOpenATRlem0p78-LUNCH-BRopgt0p5-holdtr-short"
IND = ["flow3", "fromOpen_atr", "new_lod", "ret1", "ret3", "ret12", "ret_since950_atr", "vwap_atr", "day_pos", "atr_d_pct",
       "gap_atr", "from_pc_atr", "rvol_day", "dist_pdl_atr", "rsi7", "z12", "adx7", "di_diff7", "bars_since_hod",
       "day_range_atr", "flow9prev", "flow_shift", "volumeRatio", "bar_range_atr", "sma20_dist_pct", "emaDiff", "lower_wick",
       "dist_round_atr", "ll_count6", "eff6"]
LOCK = ("2024-11-01", "2025-02-28")
# loose candidate box (the parent and every variant select inside it)
BOX = dict(lo=1030, hi=1500, adv=100e6, flow3=-0.15, fo=-0.45)
