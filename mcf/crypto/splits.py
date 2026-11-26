"""Crypto research splits, fixed 2026-11-26 BEFORE any setup was scored (docs/CRYPTO_PLAN.md).

FIT     2021-01-01 .. 2024-12-31   search / generator scoring
CHECK   2025-01-01 .. 2026-05-25   finalists scored ONCE (frozen before the look)
LOCKED  2026-05-26 .. 2026-11-25   most recent 6 months; never read in round 1. Loaders refuse it unless
                                   MCF_CRYPTO_ALLOW_LOCKED=1 (set only by the lead for a once-per-version score).
All bounds are UTC; end dates are exclusive in the code (the day after the last included day).
Educational only — not financial advice.
"""
from __future__ import annotations

import os

import pandas as pd

FIT = ("2021-01-01", "2025-01-01")
CHECK = ("2025-01-01", "2026-05-26")
LOCKED = ("2026-05-26", "2026-11-26")
LOCKED_START = LOCKED[0]
SPLITS = {"fit": FIT, "check": CHECK, "locked": LOCKED}


def locked_allowed() -> bool:
    return os.environ.get("MCF_CRYPTO_ALLOW_LOCKED") == "1"


def bounds(name: str) -> tuple[pd.Timestamp, pd.Timestamp]:
    if name == "locked" and not locked_allowed():
        raise PermissionError("crypto LOCKED block is sealed (set MCF_CRYPTO_ALLOW_LOCKED=1 only for the once-per-"
                              "version holdout score)")
    a, b = SPLITS[name]
    return pd.Timestamp(a, tz="UTC"), pd.Timestamp(b, tz="UTC")


def clip_end(end) -> pd.Timestamp:
    """Latest readable time (exclusive): the locked start unless the lock is open."""
    lim = pd.Timestamp(LOCKED_START, tz="UTC") if not locked_allowed() else pd.Timestamp.max.tz_localize("UTC")
    if end is None:
        return lim
    e = pd.Timestamp(end)
    e = e.tz_localize("UTC") if e.tzinfo is None else e
    return min(e, lim)
