"""Mechanic NM-RWN5 (Monday Weak-RS NS3 Short): shared constants. Educational only - not financial advice."""
import sys
WT = "/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/wt-wb-nmrwn5"
sys.path.insert(0, WT)
OUT = "/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/mech-nmrwn5/"
SETUP = "NM-RWN5-ns3-mon-weakrs-short"
LOCK = ("2024-11-01", "2025-02-28")
# loose candidate box: every weekday (the Monday part P4 is tested), bar close 09:50-12:30, adv20 >= $50M,
# close crosses above VWAP on this bar, stock >= 1% below its open (parent: Monday, 09:50-11:30, $95M, fromOpen < -2%)
BOX = dict(lo=950, hi=1230, adv=50e6, fo=-1.0)
COLS = ["symbol", "date", "tod", "close", "high", "low", "atr_d", "adv20", "gap", "fromOpen", "vwapDistPct", "prev_vwap",
        "sma50_dist_pct", "sma20_dist_pct", "sma20_slope_pct", "rsi", "rsi5", "heat", "flow3", "volumeRatio", "atrPct",
        "dist_lod_atr", "dist_hod_atr", "dist_pdl_atr", "dist_pdh_atr", "buyPressure", "macdPct", "emaDiff", "upper_wick",
        "lower_wick", "momentum", "rsiSlope", "pricePosition", "spy_fo", "qqq_fo", "breadth", "breadth_open", "qqq_vwap",
        "spy950", "fo950", "dow"]
