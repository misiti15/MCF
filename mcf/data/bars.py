"""Bar schema helpers.

Canonical intraday format: one DataFrame per symbol, tz-aware DatetimeIndex in
America/New_York (bar *start* time), columns open/high/low/close/volume, regular
trading hours only.
"""

from __future__ import annotations

import pandas as pd

TZ = "America/New_York"
COLUMNS = ["open", "high", "low", "close", "volume"]


def normalize(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [c.lower() for c in df.columns]
    missing = set(COLUMNS) - set(df.columns)
    if missing:
        raise ValueError(f"bars missing columns: {missing}")
    idx = pd.DatetimeIndex(df.index)
    idx = idx.tz_localize("UTC") if idx.tz is None else idx
    df.index = idx.tz_convert(TZ)
    df = df[COLUMNS].astype(float).sort_index()
    return df[~df.index.duplicated(keep="last")]


def rth(df: pd.DataFrame, open_="09:30", close="16:00") -> pd.DataFrame:
    """Keep regular-trading-hours bars (bar start in [open, close))."""
    t = df.index.time
    o, c = pd.Timestamp(open_).time(), pd.Timestamp(close).time()
    return df[(t >= o) & (t < c)]


def resample(df: pd.DataFrame, rule: str) -> pd.DataFrame:
    agg = {"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"}
    out = df.resample(rule, label="left", closed="left").agg(agg)
    return out.dropna(subset=["open"])


def daily_from_intraday(df: pd.DataFrame) -> pd.DataFrame:
    g = df.groupby(df.index.date)
    daily = pd.DataFrame(
        {
            "open": g["open"].first(),
            "high": g["high"].max(),
            "low": g["low"].min(),
            "close": g["close"].last(),
            "volume": g["volume"].sum(),
        }
    )
    daily.index = pd.to_datetime(daily.index)
    return daily
