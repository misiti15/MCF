"""Bar schema helpers.

Canonical intraday format: one DataFrame per symbol, tz-aware DatetimeIndex in
America/New_York (bar *start* time), columns open/high/low/close/volume, regular
trading hours only.
"""

from __future__ import annotations

import numpy as np
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


_CLOSE_MIN: dict[str, int] = {}


def close_min(day) -> int:
    """The exchange close of `day` in minutes since midnight ET (960 regular, 780 on a 13:00 half day), from
    mcf.execution.market_calendar.session_close (Alpaca calendar, else its known early closes). Memoised per process,
    so a live loop asks the calendar once per day. Research / display callers (Hunch, Compass) use it to drop bars at
    or after a half-day close: Alpaca prints trades until 16:00 on those days and rth()'s fixed 16:00 keeps them."""
    d = str(pd.Timestamp(str(day)).date())
    if d not in _CLOSE_MIN:
        from ..execution.market_calendar import close_minutes   # calendar only: no order / trading code

        # today / later: the Alpaca calendar (read-only GET) when keys are set, else the known list; a past day: the
        # known list only (offline, deterministic: history and tests never call out)
        today = str(pd.Timestamp.now(tz=TZ).date())
        _CLOSE_MIN[d] = int(close_minutes(d, use_http=d >= today))
    return _CLOSE_MIN[d]


def early_close_days() -> frozenset[str]:
    """Known early-close sessions (YYYY-MM-DD, close before 16:00), from the market calendar's offline list."""
    from ..execution.market_calendar import EARLY_CLOSES, PAST_EARLY_CLOSES

    return frozenset(d for d, t in {**PAST_EARLY_CLOSES, **EARLY_CLOSES}.items() if t.hour * 60 + t.minute < 960)


def next_trading_day(day, step: int = 1) -> str:
    """The next (step 1) / previous (step -1) trading day (weekends and NYSE holidays skipped), YYYY-MM-DD."""
    from ..execution.market_calendar import next_trading_day as nxt

    return nxt(day, step).isoformat()


def cap_at_close(df: pd.DataFrame, close_for=close_min) -> pd.DataFrame:
    """Drop bars that start at or after their day's exchange close (`close_for(date) -> minutes since midnight ET`).
    A regular day (close 16:00) is unchanged; on a half day the 13:00-16:00 after-hours prints go."""
    if df is None or not len(df):
        return df
    idx = df.index
    mins = idx.hour * 60 + idx.minute
    days = np.asarray(idx.date)
    lim = {d: close_for(str(d)) for d in set(days)}
    return df[np.asarray(mins) < np.array([lim[d] for d in days])]


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
