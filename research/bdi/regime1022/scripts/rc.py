"""regime1022 shared helpers. Reuses research/bdi/gates1021/scripts (common, setups, scan) unchanged; only the scratch
dir, the account list (+ Graveyard) and exit bars for every setup are new. Educational only - not financial advice.
The rule-19 locked block (2024-11-01..2025-02-28) is never read (gates1021 common asserts it)."""
from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("G21SCR", "/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/rg22")
G21 = Path(__file__).resolve().parents[2] / "gates1021" / "scripts"
sys.path.insert(0, str(G21))
import common as g21c  # noqa: E402  (gates1021/scripts/common.py)

g21c.ACCOUNTS["graveyard"] = ["account_graveyard.yaml"]
ROOT, SCR, lib, gates = g21c.ROOT, g21c.SCR, g21c.lib, g21c.gates
HERE = Path(__file__).resolve().parents[1]
TRAIN_END = g21c.TRAIN_END
no_locked, split_of = g21c.no_locked, g21c.split_of
G21SCR = Path("/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/g1021")
