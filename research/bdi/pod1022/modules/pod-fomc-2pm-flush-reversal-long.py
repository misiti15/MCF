"""pod-fomc-2pm-flush-reversal-long - FOMC-day 2 pm knee-jerk flush reversal (index ETFs, LONG).

Source: SentimenTrader 'Initial reaction to the FOMC decision' (after negative first moves since 2013 there were
several large positive reversals into the close); Quantifiable Edges (Rob Hanna, Fed-day studies) theme;
daytradingtoolkit '2 PM reversal'.
URL: https://sentimentrader.com/blog/initial-reaction-to-the-fomc-decision

NEW (event + time of day). Not a copy of cwt-c-c5-calendar (holds SPY into the announcement); this enters only AFTER
a negative 14:00 reaction.

Rules (plain English, LONG). SYMBOLS: SPY, QQQ, IWM.
  1. Today is an FOMC statement day (14:00 ET release; the FOMC calendar in _r25_util, 13 open-history days).
  2. The knee-jerk flush: the lowest low of the post-14:00 bars inside the flush window (bars 14:00-14:25, i.e. bar
     closes 14:05-14:30), as of the decision bar, is at least 0.35% below the 13:55 close.
  3. Bar close 14:15-15:15: a 5-minute close above the highs of the previous 2 bars and above the post-14:00 midpoint
     (post-14:00 low so far + 0.5 x (13:55 close - that low)).
  Entry: that bar's close. Stop (GEOM S): post-14:00 low - 0.05 x atr_d. Target: the 13:55 close (pre-announcement
  price); otherwise flat 15:55.
Harness limit (declared): the scorer clips entries at 15:00, so the window is 14:15-15:00 (not 15:15). About 8 days a
year (13 in the open history x 3 ETFs): low frequency, report n. No tweak made. Costs per config/default.yaml.
Educational only - not financial advice."""
SIDE = "long"
GEOM = "S"
WINDOW = (1415, 1500)
SYMBOLS = ["SPY", "QQQ", "IWM"]
LAYERS = ["FOMC statement day", "post-14:00 low (bars to 14:25) <= 13:55 close x (1 - 0.35%)",
          "close > highs of the prior 2 bars and > post-14:00 midpoint, 14:15-15:00",
          "stop post-14:00 low - 0.05 ATR, target 13:55 close"]

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _r25_util as U  # noqa: E402

_ST = {}


def _stash(f, i, j):
    s = _ST.get(id(f))
    if s is None or len(s[0]) != len(f):
        mask(f)
        s = _ST.get(id(f))
    return float(s[j][i]) if s is not None else float("nan")


def stop_price(f, i):
    return _stash(f, i, 0)


def target_price(f, i, stop):
    return _stash(f, i, 1)


def mask(df) -> np.ndarray:
    _ST.clear()
    n = len(df)
    z = np.zeros(n, bool)
    stop, tgt = np.full(n, np.nan), np.full(n, np.nan)
    _ST[id(df)] = (stop, tgt)
    if not n:
        return z
    b = U.base(df)
    k = U.key(df)
    tod, c, h, l, atr = b["tod"], b["c"], b["h"], b["l"], b["atr"]
    fomc = np.isin(df["date"].astype(str).to_numpy(), U.FOMC)                       # (1)
    if not fomc.any():
        return z
    c1355 = U.CB.at_tod(c, k, tod, 1355)
    # running min of lows of post-14:00 bars (closes 14:05..14:30) within the symbol-day, up to this bar
    lf = np.where((tod >= 1405) & (tod <= 1430), l, np.inf)
    st = U.start(k)
    seg = np.cumsum(st) - 1
    import pandas as pd
    lowf = pd.Series(lf).groupby(seg).cummin().to_numpy(dtype=float, copy=True)
    lowf[~np.isfinite(lowf)] = np.nan
    # post-14:00 low (any bar after 14:00 up to this one) for the midpoint and the stop
    lp = np.where(tod >= 1405, l, np.inf)
    low2 = pd.Series(lp).groupby(seg).cummin().to_numpy(dtype=float, copy=True)
    low2[~np.isfinite(low2)] = np.nan
    h1, h2 = U.lag(h, k, 1), U.lag(h, k, 2)
    with np.errstate(invalid="ignore"):
        m = fomc & (lowf <= c1355 * (1 - 0.0035))                                  # (2)
        m &= (tod >= 1415) & (tod <= 1500)
        m &= (c > h1) & (c > h2)                                                   # (3)
        m &= c > low2 + 0.5 * (c1355 - low2)
        stop[:] = low2 - 0.05 * atr
        tgt[:] = c1355
        m &= (stop < c) & (tgt > c)
    _ST[id(df)] = (stop, tgt)
    return np.asarray(m, bool)
