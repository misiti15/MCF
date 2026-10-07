"""Locked-data guard for the web_families rework. Import this BEFORE research.reddit_bt.common.

Patches BarStore.load so that (a) data/cache_q2 cannot be opened at all, and (b) rows on or after 2026-09-16
(the locked test split) are dropped by the parquet reader before they reach pandas. Asserts no locked env var is set.
Educational only - not financial advice.
"""
from __future__ import annotations

import os

import pandas as pd

from mcf.data.store import BarStore

for _v in ("MCF_LAB_ALLOW_TEST", "MCF_RBT_ALLOW_HOLDOUT", "MCF_EXITS_ALLOW_TEST"):
    assert not os.environ.get(_v), f"{_v} must not be set in a rework run"

CUT = pd.Timestamp("2026-09-16", tz="America/New_York")


def _load(self, symbol, start=None, end=None):
    if "cache_q2" in str(self.dir):
        raise PermissionError("data/cache_q2 is locked")
    p = self.path(symbol)
    if not p.exists():
        return pd.DataFrame()
    df = pd.read_parquet(p, filters=[("timestamp", "<", CUT)])
    if len(df):
        assert df.index.max() < CUT, "locked dates leaked"
    if start is not None:
        df = df[df.index >= pd.Timestamp(start, tz=df.index.tz)]
    if end is not None:
        df = df[df.index < pd.Timestamp(end, tz=df.index.tz)]
    return df


BarStore.load = _load
