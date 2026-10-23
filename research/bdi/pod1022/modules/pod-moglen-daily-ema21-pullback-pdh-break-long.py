"""pod-moglen-daily-ema21-pullback-pdh-break-long - Daily 21-EMA pullback, then the intraday prior-day-high break as
the range-breakout trigger (LONG).

Source: TraderLion - Richard Moglen, 'Trade Opportunity Case Study of the Week: PLTR 21ema Pullback and Range
Breakout' (Apr 2025) and 'BE Range Breakout' (Dec 2025: a pullback above the 21ema can still be healthy; watch for
follow-through / reconfirmation).
URL: https://traderlion.com/profile/richard-moglen/trade-opportunity-case-study-of-the-week-pltr-21ema-pullback-and-range-breakout-april-2025/

VARIANT of pod-kell-daily-ema-crossback-first-touch-long. Stated change: the entry is NOT the touch of the EMA; it is
the later intraday break of the prior day's high after a 2-5 day pullback that tagged the daily EMA21 and held it on a
closing basis.

Rules (plain English). Daily values from lib.daily() completed days (as of D-1; ATR = ATR14):
  1. Daily trend: EMA21(D-1) > SMA50(D-1); both rising (above their values 5 sessions earlier, D-6).
     Pullback: the highest high of D-10..D-1 was set on D-6..D-3, so D-1 ends a 2-5 day pullback; on some pullback
     day the low came within 0.3 x ATR of that day's EMA21 (low <= EMA21 + 0.3 ATR), and every pullback close stayed
     above EMA21 - 0.2 ATR.
  2. Today's open is below the PDH.
  3. Trigger: the first 5-min close above the PDH of the session (the 09:35-09:45 closes from the head table count:
     a break before 10:00 means no trade) must come with bar close 10:00-14:00, cumulative volume 09:30..bar >=
     1.0 x its 20-session same-time mean (_r24 rvc) and close > session VWAP; if not, no trade that day.
  4. Stop (GEOM S): the lower of the low of day and PDH - 0.5 x daily ATR. Target 2R, else flat 15:55.
No tweak used. 1 configuration. Costs per config/default.yaml (scorer). Educational only - not financial advice."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _r37_util as U  # noqa: E402
import _r36_util as U36  # noqa: E402

SIDE = "long"
GEOM = "S"
WINDOW = (1000, 1400)
LAYERS = ["daily EMA21 > SMA50, both rising", "2-5 day pullback tagged EMA21 (0.3 ATR), closes held EMA21 - 0.2 ATR",
          "open < PDH", "first close > PDH of the day at 10:00-14:00, cum vol pace >= 1.0x, above VWAP",
          "stop min(LOD, PDH - 0.5 ATR), target 2R, flat 15:55"]
_ST = {}


def compute(df):
    n = len(df)
    if not n:
        return np.zeros(0, bool), np.zeros(0), np.zeros(0)
    k = U.key(df)
    b = U.base(df)
    d = U.map_daily(df, ["e211", "sma501", "e216", "sma506", "mog1"])
    hd = U36.map_day(df, U36.head_tab(), ["c935", "c940", "c945"])
    rvc = U.R24.bars_for(df, ["rvc"])["rvc"]
    c, a, tod, pdh = b["c"], b["atr"], b["tod"], b["pdh"]
    with np.errstate(invalid="ignore", divide="ignore"):
        g = (d["e211"] > d["sma501"]) & (d["e211"] > d["e216"]) & (d["sma501"] > d["sma506"]) & (d["mog1"] == 1.0)
        g &= b["opn"] < pdh
        pre = np.fmax(np.fmax(np.nan_to_num(hd["c935"], nan=-np.inf), np.nan_to_num(hd["c940"], nan=-np.inf)),
                      np.nan_to_num(hd["c945"], nan=-np.inf))
        g &= ~(pre > pdh)
        above = c > pdh
        cs = pd.Series(above.astype(np.int64)).groupby(k).cumsum().to_numpy()
        first = above & (cs == 1)
        m = g & first & (rvc >= 1.0) & (c > b["vwap"]) & (tod >= WINDOW[0]) & (tod <= WINDOW[1])
        stop = np.fmin(b["lod"], pdh - 0.5 * a)
        R = c - stop
        m &= (R > 0) & (a > 0)
        tgt = c + 2.0 * R
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
