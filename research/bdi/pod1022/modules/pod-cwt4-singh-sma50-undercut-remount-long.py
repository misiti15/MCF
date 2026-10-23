"""pod-cwt4-singh-sma50-undercut-remount-long - Daily 50-day MA stop-run then intraday remount (LONG).

Source: Chat With Traders ep 58, Paul Singh ('Moving-average remount after a stop run'). VARIANT of CWT test B3
(stop-run reversal at prior-day / opening-range levels) and of pod-smb-daily-uptrend-sma20-intraday-touch-long
(a touch, no undercut). The change: the level is the daily SMA50 that has held for weeks; price must undercut it by
>= 1% and then remount it intraday.
URL: https://chatwithtraders.com/58

Rules (plain English). Universe: scorer liquid stocks (adv20 >= $20M), price > $10.
  1. Daily (D-1 and earlier, completed days; series restart after a > 7-day gap): close above its SMA50 on >= 10 of
     the last 15 sessions, and SMA50(D-1) > SMA50(D-11) (rising).
  2. Today the session low reached <= SMA50 x 0.99 (the stop run; fixed 1.0%, the middle of the source grid), the
     low was set by 12:30, and the stock did not gap down >= 4%.
  3. The first 5-min close back above SMA50 (the remount) within 6 bars of the bar that set the session low (a low
     set before the 09:50 frame start counts as the 09:45 bar).
  4. SPY from-open > -1.0% at the decision bar (spy_fo).
  Entry: decision bar's close (scorer; the source's next-bar open), bar close 09:50-13:00. Stop (GEOM S): session
  low - 0.1 x daily ATR. Target: the nearer of entry + 3R and the prior-day high (when it is above the entry); else
  flat 15:55. One per symbol per day.
No tweak made. The no-undercut control is not scored in this row. Costs per config/default.yaml (scorer).
Educational only - not financial advice."""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _cwt4_util as U  # noqa: E402

SIDE = "long"
GEOM = "S"
WINDOW = (950, 1300)
CONTEXT = ["spy_fo"]
UNDER = 0.99
LAYERS = [">= 10/15 closes above SMA50, SMA50 rising", "session low <= SMA50 x 0.99 by 12:30, gap > -4%",
          "first close back above SMA50 within 6 bars of the low", "spy_fo > -1.0", "price > 10",
          "stop LOD - 0.1 ATR, target min(3R, PDH)"]
_ST = {}


def mask(df) -> np.ndarray:
    n = len(df)
    z = np.zeros(n, bool)
    if n == 0 or "spy_fo" not in df:
        return z
    k = U.key(df)
    st = U.start(k)
    d = U.map_day(df, k, U.daily_basic(), ["sma50_1", "above15_1", "sma50_10_1"])
    sma = d["sma50_1"]
    b = U.base(df)
    c, lo, lod, atr, tod = b["c"], b["l"], b["lod"], b["atr"], b["tod"]
    idx = np.arange(n)
    # position of the bar that set the running session low (pre-frame low -> first row - 1)
    with np.errstate(invalid="ignore"):
        lod_p = U.lag(lod, k)
        newlow = np.where(st, lo <= lod + 1e-9, lod < lod_p - 1e-9)
    pos = np.where(newlow, idx, -1)
    first = np.where(st, idx, 0)
    first = np.maximum.accumulate(first)
    pos = np.where(st & ~newlow, idx - 1, pos)
    pos = np.maximum.accumulate(np.where(pos >= 0, pos, -1))
    pos = np.maximum(pos, first - 1)
    since = idx - pos
    lod_tod = np.where(pos >= first, tod[np.clip(pos, 0, n - 1)], 945)
    cp = U.lag(c, k)
    with np.errstate(invalid="ignore", divide="ignore"):
        m = (d["above15_1"] >= 10) & (sma > d["sma50_10_1"])
        m &= (lod <= sma * UNDER) & (lod_tod <= 1230) & (U.f(df, "gap") > -4.0)
        m &= (c > sma) & ((cp <= sma) | st) & (since >= 1) & (since <= 6)
        m &= (U.f(df, "spy_fo") > -1.0) & (c > 10)
        stop = lod - 0.1 * atr
        R = c - stop
        t3 = c + 3 * R
        pdh = b["pdh"]
        tgt = np.where((pdh > c) & (pdh < t3), pdh, t3)
    _ST[id(df)] = (stop, tgt)
    return np.asarray(m, bool)


def stop_price(f, i):
    return U.stash_get(_ST, f, mask, i, 0)


def target_price(f, i, stop):
    return U.stash_get(_ST, f, mask, i, 1)
