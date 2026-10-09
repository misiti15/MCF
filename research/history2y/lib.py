"""Loader for the 2-year lab frames (research/history2y/build_frames.py) and the session regimes.

The rule-19 locked block (2024-11-01 .. 2025-02-28, seed 20261008) lives in a separate directory and is refused
unless MCF_HIST_ALLOW_LOCKED=1 (set only by the lead when scoring a finalist once). Educational only - not financial advice.
"""
from __future__ import annotations

import os
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.dataset as ds

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "research" / "history2y" / "data"
LOCKED = ("2024-11-01", "2025-02-28")
LOCKED_MONTHS = ["2024-11", "2024-12", "2025-01", "2025-02"]
FIRST = "2024-10-01"


def _allow_locked() -> bool:
    return bool(os.environ.get("MCF_HIST_ALLOW_LOCKED"))


def months(locked: bool = False) -> list[str]:
    root = DATA / ("locked" if locked else "frames")
    return sorted(p.name.split("=", 1)[1] for p in root.glob("month=*"))


def load_month(month: str, columns: list[str] | None = None) -> pd.DataFrame:
    """One calendar month of frames, sorted by symbol, date, tod. Locked months need MCF_HIST_ALLOW_LOCKED=1."""
    locked = month in LOCKED_MONTHS
    if locked and not _allow_locked():
        raise PermissionError("the rule-19 locked block (2024-11..2025-02) is scored once per version by the lead")
    p = DATA / ("locked" if locked else "frames") / f"month={month}"
    df = ds.dataset(str(p), format="parquet").to_table(columns=columns).to_pandas()
    df["date"] = pd.to_datetime(df["date"]).dt.date
    return df.sort_values(["symbol", "date", "tod"], kind="mergesort").reset_index(drop=True)


def daily(include_locked: bool = False) -> pd.DataFrame:
    d = pd.read_parquet(DATA / "daily.parquet")
    d["date"] = pd.to_datetime(d["date"]).dt.date
    d = d[d["date"].astype(str) >= FIRST]
    if not include_locked:
        s = d["date"].astype(str)
        if not _allow_locked():
            d = d[(s < LOCKED[0]) | (s > LOCKED[1])]
    return d


def regimes(include_locked: bool = False) -> pd.DataFrame:
    """Session regimes (mcf.research.gates.session_regimes); tercile cut points from the open history only."""
    from mcf.research.gates import session_regimes

    d = daily(include_locked)
    s = d["date"].astype(str)
    open_dates = sorted(set(d.loc[(s < LOCKED[0]) | (s > LOCKED[1]), "date"]))
    return session_regimes(d, dates=open_dates)
