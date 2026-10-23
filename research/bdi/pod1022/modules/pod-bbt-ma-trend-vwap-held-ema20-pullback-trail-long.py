"""pod-bbt-ma-trend-vwap-held-ema20-pullback-trail-long - Aziz moving-average trend trade: VWAP held all morning,
first 5-min EMA20 pullback after 10:30 (LONG).

Source: Bear Bull Traders (Andrew Aziz) 'VWAP Moving Average Trend Trade: loss or hold of VWAP (after ~10:30 am)';
How to Day Trade for a Living (stop 5-10c below the MA, ride the trend until the MA breaks, 20 EMA the stronger level).
URL: https://www.goodreads.com/quotes/10440939-to-summarize-my-trading-strategy-for-vwap-moving-average-trend

VARIANT of 'Reddit R09-ema20-pullback' (first pullback to the 20 MA, full day, both sides). Stated change: VWAP must
have held all session, signals only after 10:30, long only, MA-break exit instead of a fixed target.

Rules (plain English). EMA9 / EMA20 = session EMAs of 5-minute closes seeded at the 09:35 close (r24 cache);
ATR5 = the frame's 5-minute ATR14 (atrPct x close).
  1. VWAP held: every 5-minute close from 10:00 through the entry bar is >= session VWAP.
  2. At the touch bar: EMA9 > EMA20 > VWAP and EMA20 rising over 6 bars.
  3. Pullback: the FIRST bar after 10:30 whose low comes within 0.1 x ATR5 of EMA20 (or trades below it) is the touch
     bar; it must close >= EMA20 (otherwise no trade that day).
  4. rvol_day >= 1.5 at entry (cumulative volume 09:30..bar / its 20-session same-time mean).
  5. SPY not below its own VWAP at the entry bar (SPY's frame vwapDistPct >= 0).
  Entry: the first later bar that closes above the touch-bar high (no close below EMA20 in between); the scorer enters
  at that close (= next-bar open). Bar close 10:35-14:30 ET for both the touch and the entry.
  Stop (GEOM S): EMA20 - 0.1 x ATR5 at entry, fixed. Exit: the scorer cannot trail on 'first 5-minute close below
  EMA20', so the trade holds to the fixed stop or 15:55 (no target) - a stated deviation; the EMA9-trail variant is
  not scored for the same reason.
No tweak used. Costs per config/default.yaml (scorer). Only bars up to the decision bar are used.
Educational only - not financial advice."""
import sys
from pathlib import Path

import numba
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _r31_util as U  # noqa: E402

SIDE = "long"
GEOM = "S"
WINDOW = (1035, 1430)
LAYERS = ["every close >= VWAP since 10:00", "EMA9 > EMA20 > VWAP, EMA20 6-bar slope > 0",
          "first EMA20 touch after 10:30 (low <= EMA20 + 0.1 ATR5, close >= EMA20)", "close > touch-bar high",
          "rvol_day >= 1.5", "SPY >= its VWAP", "stop EMA20 - 0.1 ATR5, hold to 15:55", "10:35-14:30 ET"]
_ST = {}


@numba.njit(cache=False)
def _k(b, e, tod, c, h, l, vd, vw, e9, e20, atr5, rvc, spyvd, w0, w1):
    n = len(c)
    m = np.zeros(n, np.bool_)
    stop = np.full(n, np.nan)
    for s in range(len(b)):
        i0, i1 = b[s], e[s]
        tj = -1
        for i in range(i0, i1):
            if tod[i] >= 1000 and not (vd[i] >= 0):
                break
            if tod[i] <= 1030:
                continue
            if tod[i] > w1:
                break
            if tj < 0:
                if l[i] <= e20[i] + 0.1 * atr5[i]:
                    good = c[i] >= e20[i] and e9[i] > e20[i] and e20[i] > vw[i] and i - 6 >= i0 and \
                        e20[i] - e20[i - 6] > 0
                    if not good:
                        break
                    tj = i
                continue
            if c[i] > h[tj]:
                sp = e20[i] - 0.1 * atr5[i]
                if rvc[i] >= 1.5 and spyvd[i] >= 0 and sp < c[i]:
                    m[i] = True
                    stop[i] = sp
                break
            if c[i] < e20[i]:
                break
    return m, stop


def compute(df):
    b = U.base(df)
    k = U.key(df)
    si = U.sess_ind(df)
    c = b["c"]
    atr5 = U.f(df, "atrPct") / 100 * c
    spyvd = U.spy_rows(df, ["vwapDistPct"])["vwapDistPct"]
    bb, ee = U.segments(k)
    return _k(bb, ee, b["tod"], c, b["h"], b["l"], U.f(df, "vwapDistPct"), b["vwap"], si["e9"], si["e20"], atr5,
              si["rvc"], spyvd, WINDOW[0], WINDOW[1])


def mask(df):
    m, s = compute(df)
    _ST.clear()
    _ST[id(df)] = s
    return m


def stop_price(f, i):
    s = _ST.get(id(f))
    if s is None or len(s) != len(f):
        mask(f)
        s = _ST[id(f)]
    return float(s[i])
