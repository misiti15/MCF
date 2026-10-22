"""l3_1022 shared helpers: scratch dir, regime1022 helpers (labels, live journals) reused unchanged.
Educational only - not financial advice. The locked block 2024-11-01..2025-02-28 is never read."""
from __future__ import annotations

import os
import sys
from pathlib import Path

SCRATCH = Path("/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/l3_1022")
SCRATCH.mkdir(parents=True, exist_ok=True)
os.environ["G21SCR"] = str(SCRATCH)          # regime1022/gates1021 helpers write their scratch here
HERE = Path(__file__).resolve().parents[1]
R22 = HERE.parent / "regime1022" / "scripts"
sys.path.insert(0, str(R22))
import rc  # noqa: E402,F401  (regime1022 rc -> gates1021 common; asserts the locked block stays closed)

SETUP = "L3-gap-slope-fromopen-FD"
