"""pod-qs-tlt-monthend-intraday-long - TLT month-end window: intraday VWAP-reclaim long on the last 5 trading days
of the month.

Source: Quantified Strategies, 'Long-term Treasuries calendar effects' (buy the close of the 7th-last trading day,
sell the last trading day's close; the first 7 days of the month are negative); also Kris Longmore on The
Algorithmic Advantage (bond end-of-month effect).
URL: https://quantifiedstrategies.substack.com/p/long-term-treasuries-calendar-effects

NEW (no TLT calendar setup exists; pod-cal-monthend-rebalance-contra-index trades SPY/QQQ against the MTD move and
pod-cal-tom trades stocks at the turn of the month).
Rules (plain English, LONG). SYMBOLS TLT.
  1. Today is one of the last 5 NYSE trading days of the month (hard-coded calendar, as in the monthend module).
  2. TLT's prior daily close >= its 50-day SMA x 0.98 (not a collapsing bond tape), lib.daily() completed days.
  3. Trigger: a bar closing 10:00-13:00 with vwapReclaim == +1 (close above VWAP after being at or below it 3 bars
     earlier) and fromOpen > -0.30%.
  4. RSI(14) on 5m < 65 on the trigger bar.
  Entry: that bar's close (the first qualifying bar per day). Stop (GEOM S): low of day - 0.05 x atr_d, with the
  risk floored at 0.20 x atr_d (stop = min(LOD - 0.05 ATR, entry - 0.20 ATR)). Target: none, flat 15:55 (the source
  holds through the window; this is the intraday slice).
Pre-declared configurations (3): this main; -ctrl-mid (the same rule on trading days 6-15 of the month, the control);
-gld (the same rule on GLD, the cross-asset control). No tweak made. Trade count is low (~5 per month).
Costs per config/default.yaml (scorer). Only bars up to the decision bar and completed days are used.
Educational only - not financial advice."""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _r38_util as U  # noqa: E402

SIDE = "long"
GEOM = "S"
WINDOW = (1000, 1300)
TRADE = "TLT"
SYMBOLS = [TRADE]
CONTEXT = []
DAYS = "last5"
LAYERS = ["last 5 trading days of the month", "D-1 close >= 0.98 x SMA50 (daily)",
          "vwapReclaim == +1, fromOpen > -0.30%, 10:00-13:00", "rsi < 65",
          "stop LOD - 0.05 ATR (risk >= 0.20 ATR), flat 15:55"]
_ST = {}


def _compute(df):
    n = len(df)
    b = U.base(df)
    c, atr, tod = b["c"], b["atr"], b["tod"]
    cal = U.tdom()
    ds = df["date"].astype(str).to_numpy()
    if DAYS == "last5":
        dm = np.array([cal.get(x, (0, 99))[1] <= 5 for x in ds], bool)
    else:
        dm = np.array([6 <= cal.get(x, (0, 99))[0] <= 15 for x in ds], bool)
    c1, s1 = U.daily_sma(df, TRADE, 50)
    with np.errstate(invalid="ignore"):
        m = dm & (df["symbol"].astype(str).to_numpy() == TRADE)
        m &= c1 >= 0.98 * s1
        m &= (U.f(df, "vwapReclaim") == 1) & (U.f(df, "fromOpen") > -0.30)
        m &= U.f(df, "rsi") < 65
        m &= (tod >= WINDOW[0]) & (tod <= WINDOW[1]) & (atr > 0)
        stop = np.minimum(b["lod"] - 0.05 * atr, c - 0.20 * atr)
    return np.asarray(m, bool), stop


def mask(df):
    m, s = _compute(df)
    _ST.clear()
    _ST[id(df)] = s
    return m


def stop_price(f, i):
    s = _ST.get(id(f))
    if s is None or len(s) != len(f):
        mask(f)
        s = _ST[id(f)]
    return float(s[i])
