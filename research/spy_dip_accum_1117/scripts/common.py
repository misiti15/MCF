"""Shared loaders for research/spy_dip_accum_1117. Locked block 2024-11-01..2025-02-28 is dropped at load.
Educational only - not financial advice."""
from __future__ import annotations

import os
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(os.environ.get("MCF_ROOT", "/home/user/MCF"))
HERE = Path(__file__).resolve().parents[1]
LOCK = (pd.Timestamp("2024-11-01"), pd.Timestamp("2025-02-28"))
LAST_DAILY = pd.Timestamp("2026-11-16")          # 2026-11-17 is a partial session
SEG = {"A": (pd.Timestamp("2016-01-04"), pd.Timestamp("2024-10-31")),
       "B": (pd.Timestamp("2025-03-03"), LAST_DAILY)}
LEV = {"SPY": 1, "SSO": 2, "SPXL": 3, "UPRO": 3}
ETFS = ["SPY", "SPXL", "UPRO", "SSO"]


def load_daily(path):
    d = pd.read_parquet(path)
    d = d[(d.date <= LAST_DAILY) & ~d.date.between(*LOCK)]
    out = {}
    for f in ["open", "high", "low", "close"]:
        out[f] = d.pivot(index="date", columns="symbol", values=f).sort_index()
    return out


def load_minute(sym, last=pd.Timestamp("2026-11-04")):
    m = pd.read_parquet(ROOT / "data/cache_hist/1Min" / f"{sym}.parquet")
    day = m.index.tz_localize(None).normalize()
    keep = ~((day >= LOCK[0]) & (day <= LOCK[1])) & (day <= last)
    m = m[keep].copy()
    m["day"] = np.asarray(day[keep])
    m["hm"] = m.index.hour * 100 + m.index.minute
    return m[(m.hm >= 930) & (m.hm <= 1559)]
