"""Mechanic NM-ETF-late-dip-di-long: shared constants. Educational only - not financial advice."""
import importlib.util, sys
sys.path.insert(0, "/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/wt-wb-nmetf")
OUT = "/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/mech-nmetf/"
_spec = importlib.util.spec_from_file_location("mod", "/home/user/MCF/research/swarm1017/arena-index-etf/modules/AR-ETF-late-dip-di-long.py")
MOD = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(MOD)
SYMS = sorted(MOD.SYMBOLS)
IND = ["ret3", "di_diff7", "atr_d_pct", "adx7", "vwap_atr", "day_pos", "fromOpen_atr", "from_pc_atr", "rvol_day", "ret12",
       "ret_since950_atr", "bars_since_lod", "rsi7", "z12", "gap_atr", "dist_lod_atr", "ret6", "ret1", "emaDiff", "eff6"]
LOCK = ("2024-11-01", "2025-02-28")
