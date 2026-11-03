"""ex30/micro shared helpers for the microstructure / bar-shape lab modules (research/bdi/ex30/micro).
Every look-back stays inside one symbol-day; live frames (one symbol-day, bars from 09:35) and offline frames (many
symbol-days, bars from 09:50) give the same values inside each module's window. Educational only - not financial advice."""
import numpy as np
import pandas as pd


def col(df, k):
    return df[k].to_numpy(dtype=float) if k in df else np.full(len(df), np.nan)


def segments(df):
    """Integer symbol-day id per row (frames are sorted by symbol, date, tod)."""
    if "symbol" in df and "date" in df:
        key = df["symbol"].astype(str).to_numpy() + "|" + df["date"].astype(str).to_numpy()
        return np.cumsum(np.r_[True, key[1:] != key[:-1]])
    return np.ones(len(df), int)


def lag(x, seg, n=1):
    x = np.asarray(x, float)
    if n >= len(x):
        return np.full(len(x), np.nan)
    p = np.r_[np.full(n, np.nan), x[:-n]]
    ps = np.r_[np.full(n, -1), seg[:-n]]
    p[ps != seg] = np.nan
    return p


def colour(df):
    """+1 green body, -1 red body, 0 doji (body < 5% of range) or zero-range bar; recovered from the wick columns."""
    c, h, l = col(df, "close"), col(df, "high"), col(df, "low")
    uw, lw = col(df, "upper_wick"), col(df, "lower_wick")
    with np.errstate(invalid="ignore", divide="ignore"):
        pos = (c - l) / (h - l)
        body = 1 - uw - lw
        green = np.abs(pos - (1 - uw)) <= np.abs(pos - lw)
        out = np.where(green, 1, -1)
        out[~(body >= 0.05)] = 0
    return out


def seg_cumsum(x, seg):
    """Running sum of x inside each symbol-day."""
    return pd.Series(np.asarray(x, float)).groupby(seg).cumsum().to_numpy()
