"""Mechanic CWT09-gapdn-vwaploss-g10-short: shared paths / constants. Educational only - not financial advice."""
OUT = "/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/mech-cwt09g10/"
SETUP = "CWT09-gapdn-vwaploss-g10-short"
LOCK = ("2024-11-01", "2025-02-28")
REPLAY = ("2026-10-12", "2026-11-13")     # the setup's live sessions (Testing 2 from 10-12 .. On Deck to 11-13)
TWO_Y = ("2024-10-01", "2026-10-09")       # 2-year lab frames, open months only, before the replay window
TRAIN_END = "2025-12-31"
GAP_LOOSE = 7.0                            # candidate superset: gap <= -7% (every variant uses >= 8%)
from pathlib import Path as _P
CODE_ROOT = str(_P(__file__).resolve().parents[4])   # the repo checkout holding this file (mcf package)
