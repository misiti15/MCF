"""ns3var1022 shared helpers. Educational only - not financial advice. The rule-19 locked block
(2024-11-01..2025-02-28) is never read: frames come from research/history2y/lib, which refuses the locked months."""
from __future__ import annotations

import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "research" / "history2y"))
import lib  # noqa: E402

assert not os.environ.get("MCF_HIST_ALLOW_LOCKED"), "ns3var1022 never reads the locked block"
SP = Path("/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad")
NV = SP / "nv22"
NV.mkdir(parents=True, exist_ok=True)
G21SCR = SP / "g1021"
RG22 = SP / "rg22"
TRAIN_END = pd.Timestamp("2025-12-31").date()
LOCK = (pd.Timestamp("2024-11-01").date(), pd.Timestamp("2025-02-28").date())


def no_locked(dates) -> None:
    d = pd.to_datetime(pd.Series(dates)).dt.date
    assert not ((d >= LOCK[0]) & (d <= LOCK[1])).any(), "locked block row found"


def split_of(dates) -> np.ndarray:
    d = pd.to_datetime(pd.Series(dates)).dt.date.to_numpy()
    return np.where(d <= TRAIN_END, "train", "valid")
