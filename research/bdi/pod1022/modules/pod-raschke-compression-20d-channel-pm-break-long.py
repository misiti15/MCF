"""pod-raschke-compression-20d-channel-pm-break-long - Volatility compression near the 20-day high, afternoon break
of the channel (LONG).

Source: 'Raschke Trade Sheet (scanner)', TradingView (momentum bias + volatility compression + 20-day channel test
agreeing = candidate); Raschke / Crabel contraction-to-expansion cycle.
URL: https://id.tradingview.com/script/8MVLfKu4-Raschke-Trade-Sheet-scanner/

VARIANT of pod-smb-20d-high-time-acceptance-long and pod-raschke-first-pullback-after-20d-high-long. Stated change: a
compression gate is required, the break must come in the afternoon, and there is no pullback or time-acceptance wait.

Rules (plain English). Daily values from lib.daily() completed days (as of D-1; ATRn = mean true range of n days):
  1. Momentum bias: close(D-1) > SMA20(D-1) and SMA20(D-1) > SMA20(D-6) (rising over 5 days).
  2. Compression: ATR5 / ATR20 <= 0.7 (as of D-1), and the ranges of D-1, D-2, D-3 are each below ATR20; the prior
     close is within 0.5 x ATR20 of the 20-day high (max high of D-20..D-1).
  3. Morning 09:30-12:30: the high of day as of the 12:30 bar is still below the 20-day high, and >= 60% of the
     frame bars closing 09:50..12:30 closed above session VWAP (frames start at 09:50 - stated proxy).
  4. Trigger: the first 5-min close above the 20-day high with bar close 12:35-15:00 (after (3) it is the first of
     the day), with SPY above its session VWAP on that bar (SPY's own frame vwapDistPct > 0). If SPY is below, no
     trade that day (strict 'first close').
  5. Stop (GEOM S): the lower of session VWAP and the low of the bars closing 12:05..trigger, minus 0.05 x daily ATR.
     Target 1.5R, else flat 15:55.
No tweak used. 1 configuration. Costs per config/default.yaml (scorer). Educational only - not financial advice."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _r37_util as U  # noqa: E402

SIDE = "long"
GEOM = "S"
WINDOW = (1235, 1500)
CONTEXT = ["spy_vwap (SPY frame vwapDistPct)"]
LAYERS = ["close > SMA20 rising 5d", "ATR5/ATR20 <= 0.7, last 3 ranges < ATR20, close within 0.5 ATR20 of 20d high",
          "HOD at 12:30 < 20d high, >= 60% of 09:50-12:30 bars above VWAP",
          "first close > 20d high 12:35-15:00, SPY above VWAP",
          "stop min(VWAP, low since 12:00) - 0.05 ATR, target 1.5R, flat 15:55"]
_ST = {}


def compute(df):
    n = len(df)
    if not n:
        return np.zeros(0, bool), np.zeros(0), np.zeros(0)
    k = U.key(df)
    b = U.base(df)
    d = U.map_daily(df, ["c1", "sma201", "sma206", "atr51", "atr201", "rng1", "rng2", "rng3", "hi201"])
    spy = U.spy_rows(df, ["vwapDistPct"])["vwapDistPct"]
    c, h, l, a, tod = b["c"], b["h"], b["l"], b["atr"], b["tod"]
    hi = d["hi201"]
    with np.errstate(invalid="ignore", divide="ignore"):
        g = (d["c1"] > d["sma201"]) & (d["sma201"] > d["sma206"])
        g &= (d["atr51"] / d["atr201"] <= 0.7)
        g &= (d["rng1"] < d["atr201"]) & (d["rng2"] < d["atr201"]) & (d["rng3"] < d["atr201"])
        g &= (hi - d["c1"] <= 0.5 * d["atr201"])
        am = tod <= 1230
        n_am = pd.Series(am.astype(float)).groupby(k).transform("sum").to_numpy()
        n_up = pd.Series((am & (c > b["vwap"])).astype(float)).groupby(k).transform("sum").to_numpy()
        hod1230 = U.C3.at_tod(b["hod"], k, tod, 1230)
        g &= (hod1230 < hi) & (n_am >= 1) & (n_up >= 0.6 * n_am)
        # first close above the 20d high after 12:30
        above = (tod >= 1235) & (c > hi)
        cs = pd.Series(above.astype(np.int64)).groupby(k).cumsum().to_numpy()
        first = above & (cs == 1)
        m = g & first & (spy > 0) & (tod >= WINDOW[0]) & (tod <= WINDOW[1])
        lw = np.where(tod >= 1205, l, np.inf)
        pml = pd.Series(lw).groupby(k).cummin().to_numpy()
        stop = np.fmin(b["vwap"], pml) - 0.05 * a
        R = c - stop
        m &= (R > 0) & (a > 0)
        tgt = c + 1.5 * R
    return np.asarray(m, bool), stop, tgt


def mask(df):
    m, s, t = compute(df)
    _ST.clear()
    _ST[id(df)] = (s, t)
    return m


def _get(f):
    s = _ST.get(id(f))
    if s is None or len(s[0]) != len(f):
        mask(f)
        s = _ST[id(f)]
    return s


def stop_price(f, i):
    return float(_get(f)[0][i])


def target_price(f, i, stop):
    return float(_get(f)[1][i])
