"""Shared helpers for research/bdi/reddit1021 (see PLAN.md). Educational only - not financial advice.

The rule-19 locked block (2024-11-01..2025-02-28) is never read: regular-hours 1-minute files are read with pyarrow
row filters that keep only rows outside the block (as research/bdi/longs1020), the extended-hours fetch never requests
it, and every loader asserts that no locked date survives. MCF_HIST_ALLOW_LOCKED must be unset."""
from __future__ import annotations

import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "research" / "history2y"))

assert not os.environ.get("MCF_HIST_ALLOW_LOCKED"), "reddit1021 never reads the locked block"

HERE = Path(__file__).resolve().parents[1]
SCR = Path(os.environ.get("R21SCR", "/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/r1021"))
SCR.mkdir(parents=True, exist_ok=True)
H1 = ROOT / "data" / "cache_hist" / "1Min"
TZ = "America/New_York"
LOCK = (pd.Timestamp("2024-11-01").date(), pd.Timestamp("2025-02-28").date())
LOCK_A = pd.Timestamp("2024-11-01", tz=TZ)
LOCK_B = pd.Timestamp("2025-03-01", tz=TZ)
TRAIN_END = pd.Timestamp("2025-12-31").date()


def assert_open(dates) -> None:
    d = np.asarray(pd.to_datetime(pd.Series(list(dates))).dt.date)
    assert not ((d >= LOCK[0]) & (d <= LOCK[1])).any(), "locked block row found"


def split_of(dates) -> np.ndarray:
    d = pd.to_datetime(pd.Series(list(dates))).dt.date.to_numpy()
    return np.where(d <= TRAIN_END, "train", "valid")


def load_rth(sym: str) -> pd.DataFrame | None:
    """Regular-hours 1-minute bars of `sym` outside the locked block (row filter applied while reading)."""
    f = H1 / f"{sym}.parquet"
    if not f.exists():
        return None
    col = "__index_level_0__"
    t = pq.read_table(f, filters=[[(col, "<", LOCK_A)], [(col, ">=", LOCK_B)]])
    df = t.to_pandas()
    if not len(df):
        return None
    df = df.between_time("09:30", "15:59")
    assert_open(df.index.date)
    return df


def load_ext(sym: str, tf: str = "1Min") -> pd.DataFrame | None:
    f = SCR / f"ext_{tf}" / f"{sym}.parquet"
    if not f.exists():
        return None
    df = pd.read_parquet(f)
    assert_open(df.index.date)
    return df
