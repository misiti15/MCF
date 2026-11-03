"""ex30/levels shared helpers for the price-level / magnet lab modules (research/bdi/ex30/levels).
Levels used are only those the live runner has on the lab frame: today's open (close / (1 + fromOpen/100)), the prior
close (open / (1 + gap/100); live: ctx.prev_close), the running high of day (close + dist_hod_atr x atr_d; includes the
09:30-09:50 bars in live and offline frames alike), session VWAP (close / (1 + vwapDistPct/100)) and round numbers
computed from price. Every look-back stays inside one symbol-day and only reads bars with close >= 09:50, so live frames
(bars from 09:35) and offline frames (bars from 09:50) agree inside each module's window.
Educational only - not financial advice."""
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


def step(px):
    """Round-number grid by price: $10 at >= 200, $5 at 50-200, $1 at 10-50, $0.50 below 10."""
    px = np.asarray(px, float)
    return np.where(px >= 200, 10.0, np.where(px >= 50, 5.0, np.where(px >= 10, 1.0, 0.5)))


def levels(df):
    """dict of the level arrays: open, pclose, hod (cents-rounded), vwap."""
    c, atr = col(df, "close"), col(df, "atr_d")
    with np.errstate(invalid="ignore", divide="ignore"):
        o = c / (1 + col(df, "fromOpen") / 100)
        pc = o / (1 + col(df, "gap") / 100)
        hod = np.round(c + col(df, "dist_hod_atr") * atr, 2)
        vw = c / (1 + col(df, "vwapDistPct") / 100)
    return {"open": o, "pclose": pc, "hod": hod, "vwap": vw}


def window(df, w):
    tod = col(df, "tod")
    return (tod >= w[0]) & (tod <= w[1])
