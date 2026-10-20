"""Shared loaders / simulator for research/bdi/longs1020 (see PLAN.md). Educational only - not financial advice.

The rule-19 locked block (2024-11-01..2025-02-28) is never read: 1-minute files are read with pyarrow row filters
that keep only rows outside the block, and lab frames come from research/history2y/lib (which refuses it)."""
from __future__ import annotations

import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "research" / "history2y"))
import lib  # noqa: E402

from mcf.research import gates  # noqa: E402

HERE = Path(__file__).resolve().parents[1]
SCR = Path(os.environ.get("L20SCR", "/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/longs1020"))
SCR.mkdir(parents=True, exist_ok=True)
H1 = ROOT / "data" / "cache_hist" / "1Min"
TZ = "America/New_York"
LOCK_A = pd.Timestamp("2024-11-01", tz=TZ)
LOCK_B = pd.Timestamp("2025-03-01", tz=TZ)
TRAIN_END = pd.Timestamp("2025-12-31").date()


def load_1min(sym: str) -> pd.DataFrame | None:
    """RTH 1-minute bars of `sym` outside the locked block (filter applied while reading)."""
    f = H1 / f"{sym}.parquet"
    if not f.exists():
        return None
    col = "__index_level_0__"
    flt = [[(col, "<", LOCK_A)], [(col, ">=", LOCK_B)]]
    t = pq.read_table(f, filters=flt)
    df = t.to_pandas()
    if not len(df):
        return None
    df = df.between_time("09:30", "15:59")
    d = df.index.date
    assert not ((d >= pd.Timestamp("2024-11-01").date()) & (d <= pd.Timestamp("2025-02-28").date())).any()
    return df


def split_of(dates) -> np.ndarray:
    d = pd.to_datetime(pd.Series(dates)).dt.date.to_numpy()
    return np.where(d <= TRAIN_END, "train", "valid")


def regimes() -> pd.Series:
    return lib.regimes()["regime"]


def cost_r(kind, px, R, tod, tier):
    """Production cost in R for a 1-min-simulated trade: entry side x tod multiplier, exit side unless a target
    (limit) fill (kind 2), +2c on stop fills (kind 1), x tier (3 on the extended tier)."""
    kind = np.asarray(kind)
    em = gates.tod_cost_mult(tod)
    side = gates.SLIP_PS + np.asarray(px, float) * gates.SLIP_BPS
    c = side * em + np.where(kind == 2, 0.0, side) + np.where(kind == 1, gates.STOP_EXTRA, 0.0)
    return np.asarray(tier, float) * c / np.asarray(R, float)


def sim_day(o, h, l, c, mins, entry_min, R, mode: str):
    """One long trade on one day's 1-minute arrays (minutes since 09:30 = bar start). Entry at the open of the first
    bar with start >= entry_min. Returns (gross_R, stop_flag, entry_px) or None. mode: holdtr | time60 | t1s1 | t05s1."""
    i0 = np.searchsorted(mins, entry_min)
    if i0 >= len(mins) or R <= 0:
        return None
    e = o[i0]
    stop = e - R
    best = e
    last = np.searchsorted(mins, 385, side="right") - 1          # bar starting 15:55 -> flatten at its close
    if mode == "time60":
        last = min(last, np.searchsorted(mins, mins[i0] + 60, side="left") - 1)
    tgt = {"t1s1": e + R, "t05s1": e + 0.5 * R}.get(mode)
    for i in range(i0, max(i0, last) + 1):
        if l[i] <= stop:
            px = min(o[i], stop)
            return (px - e) / R, 1, e
        if tgt is not None and h[i] >= tgt:
            return (max(o[i], tgt) - e) / R if o[i] > tgt else (tgt - e) / R, 2, e
        if h[i] > best:
            best = h[i]
        if mode == "holdtr" and best - e >= R:
            stop = max(stop, best - R)
    return (c[min(last, len(c) - 1)] - e) / R, 0, e
