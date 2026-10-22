"""st7_1022 shared helpers (PLAN.md). Educational only - not financial advice.
The rule-19 locked block (2024-11-01..2025-02-28) is never read: frames come from research/history2y/lib (refuses the
locked months); the 1-minute cache is read with a pyarrow row filter that excludes the block; loaders assert."""
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

from mcf.research import gates  # noqa: E402
from mcf.research.gates import SLIP_BPS, SLIP_PS, STOP_EXTRA, tod_cost_mult  # noqa: E402,F401

assert not os.environ.get("MCF_HIST_ALLOW_LOCKED"), "st7_1022 never reads the locked block"
SP = Path("/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad")
W = SP / "st7"
W.mkdir(parents=True, exist_ok=True)
RG22 = SP / "rg22"
TRAIN_END = pd.Timestamp("2025-12-31").date()
LOCK = (pd.Timestamp("2024-11-01").date(), pd.Timestamp("2025-02-28").date())
NP = 74  # forward 5-minute bars stored (09:55..15:55)


def no_locked(dates) -> None:
    d = pd.to_datetime(pd.Series(list(dates))).dt.date
    assert not ((d >= LOCK[0]) & (d <= LOCK[1])).any(), "locked block row found"


def split_of(dates) -> np.ndarray:
    d = pd.to_datetime(pd.Series(list(dates))).dt.date.to_numpy()
    return np.where(d <= TRAIN_END, "train", "valid")


def summ(r, dates) -> dict:
    t = pd.DataFrame({"date": list(dates), "r": np.asarray(r, float)})
    return gates.summary(t)


def tier(close, gap) -> np.ndarray:
    return np.where((np.abs(np.asarray(gap, float)) >= 20) | (np.asarray(close, float) < 5), 3.0, 1.0)
