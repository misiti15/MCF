"""Indicator/feature calculations. All functions are causal: value at bar i uses bars <= i only."""

from __future__ import annotations

import numpy as np
import pandas as pd


def vwap(day: pd.DataFrame) -> pd.Series:
    tp = (day["high"] + day["low"] + day["close"]) / 3
    cv = day["volume"].cumsum().replace(0, np.nan)
    return (tp * day["volume"]).cumsum() / cv


def vwap_std(day: pd.DataFrame, vw: pd.Series | None = None) -> pd.Series:
    """Volume-weighted standard deviation of typical price around session VWAP."""
    vw = vwap(day) if vw is None else vw
    tp = (day["high"] + day["low"] + day["close"]) / 3
    cv = day["volume"].cumsum().replace(0, np.nan)
    var = (day["volume"] * tp**2).cumsum() / cv - vw**2
    return np.sqrt(var.clip(lower=0))


def rsi(close: pd.Series, n: int = 14) -> pd.Series:
    d = close.diff()
    up = d.clip(lower=0).ewm(alpha=1 / n, adjust=False).mean()
    dn = (-d.clip(upper=0)).ewm(alpha=1 / n, adjust=False).mean()
    rs = up / dn.replace(0, np.nan)
    return (100 - 100 / (1 + rs)).fillna(100.0)


def atr(daily: pd.DataFrame, n: int = 14) -> pd.Series:
    pc = daily["close"].shift()
    tr = pd.concat(
        [daily["high"] - daily["low"], (daily["high"] - pc).abs(), (daily["low"] - pc).abs()], axis=1
    ).max(axis=1)
    return tr.rolling(n, min_periods=n).mean()


def minute_of_session(idx: pd.DatetimeIndex, open_hour=9, open_minute=30) -> np.ndarray:
    return (idx.hour * 60 + idx.minute) - (open_hour * 60 + open_minute)


def cum_volume_profile(intraday: pd.DataFrame) -> pd.DataFrame:
    """Rows = session dates, columns = minute-of-session, values = cumulative volume."""
    mos = minute_of_session(intraday.index)
    tbl = pd.DataFrame(
        {"date": intraday.index.date, "mos": mos, "v": intraday["volume"].to_numpy()}
    ).pivot_table(index="date", columns="mos", values="v", aggfunc="sum")
    return tbl.fillna(0).cumsum(axis=1)


def opening_range(day: pd.DataFrame, minutes: int) -> tuple[float, float, int]:
    """(high, low, index of last bar in range). Requires bars in the first `minutes`."""
    mos = minute_of_session(day.index)
    mask = mos < minutes
    if not mask.any():
        return np.nan, np.nan, -1
    rng = day[mask]
    return float(rng["high"].max()), float(rng["low"].min()), int(np.flatnonzero(mask)[-1])
