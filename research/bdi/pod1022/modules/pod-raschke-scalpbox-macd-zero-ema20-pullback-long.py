"""pod-raschke-scalpbox-macd-zero-ema20-pullback-long - EMA20 pullback while the 5-min MACD line holds above zero,
reversal-bar entry (Raschke scalping box, LONG side; the SHORT mirror is the companion -short module).

Source: TradingView 'Linda Raschke Scalping - Box Signal' (EMA 20 + MACD zero-line setup); Raschke rule list ('buy
the first pullback after a new high').
URL: https://de.tradingview.com/script/MRWtng3L-Linda-Raschke-Scalping-Box-Signal/

VARIANT of the Reddit R09-ema20-pullback ('first pullback to the 20 MA in a trend'). What changes: the trend gate is
the MACD line staying above zero (>= 12 bars, never crossing zero during the pullback) instead of a slope test,
multiple pullbacks are allowed, and entry is a reversal-bar trigger.

Rules (plain English). EMA20 and the MACD line (EMA12 - EMA26 of 5m closes) are computed continuously over the
full-session 5m bars (09:35-15:55, across days, previous month as warm-up; _r36_util.ema_macd).
  LONG:
  1. Touch bar t: the MACD line has been > 0 for >= 12 consecutive bars ending at t.
  2. Bar t's low touches or pierces EMA20 by at most 0.15 x daily ATR (EMA20 - 0.15 ATR <= low <= EMA20).
  3. Entry bar j in t+1..t+3: the first close above the prior bar's high, the MACD line > 0 on every bar t..j, and
     the close is above session VWAP. Entry bar close 10:15-15:00.
  4. Stop: pullback low (lowest low t..j) - 0.05 x ATR. Target: 1.5R. Flat 15:55.
  SHORT (companion): mirror - MACD < 0 for >= 12 bars, the bar high rallies into EMA20 (EMA20 <= high <= EMA20 +
  0.15 ATR), first close below the prior bar's low within 3 bars, MACD < 0 throughout, close below VWAP; stop
  pullback high + 0.05 ATR, target 1.5R. The two sides are reported separately.
Multiple pullbacks per day are allowed in the rule, but the scorer takes the first qualifying entry per symbol-day.
No tweak made. 2 configurations (long / short). Costs per config/default.yaml (scorer).
Educational only - not financial advice."""
import sys
from pathlib import Path

import numba
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _r36_util as U  # noqa: E402

SIDE = "long"
GEOM = "S"
WINDOW = (1015, 1500)
LAYERS = ["MACD line > 0 for >= 12 bars", "low touches EMA20 (pierce <= 0.15 ATR)",
          "close > prior bar high within 3 bars, MACD > 0 throughout", "close > VWAP", "10:15-15:00",
          "stop pullback low - 0.05 ATR, target 1.5R"]
_ST = {}


@numba.njit(cache=False)
def _k(b, e, tod, c, h, l, e20, md, cntp, cntn, vw, atr, sgn, w0, w1):
    n = len(c)
    m = np.zeros(n, np.bool_)
    stop = np.full(n, np.nan)
    tgt = np.full(n, np.nan)
    for s in range(len(b)):
        i0, i1 = b[s], e[s]
        for t in range(i0, i1):
            a = atr[t]
            if not (a > 0) or not (e20[t] == e20[t]):
                continue
            if sgn == 1:
                if not (cntp[t] >= 12 and l[t] <= e20[t] and l[t] >= e20[t] - 0.15 * a):
                    continue
            else:
                if not (cntn[t] >= 12 and h[t] >= e20[t] and h[t] <= e20[t] + 0.15 * a):
                    continue
            ext = l[t] if sgn == 1 else h[t]
            for j in range(t + 1, min(t + 4, i1)):
                if sgn == 1:
                    if not (md[j] > 0):
                        break
                    ext = min(ext, l[j])
                    trig = c[j] > h[j - 1]
                    side_ok = c[j] > vw[j]
                else:
                    if not (md[j] < 0):
                        break
                    ext = max(ext, h[j])
                    trig = c[j] < l[j - 1]
                    side_ok = c[j] < vw[j]
                if not trig:
                    continue
                if side_ok and tod[j] >= w0 and tod[j] <= w1 and not m[j]:
                    sp = ext - sgn * 0.05 * a
                    R = sgn * (c[j] - sp)
                    if R > 0:
                        m[j] = True
                        stop[j] = sp
                        tgt[j] = c[j] + sgn * 1.5 * R
                break        # the first close beyond the prior bar decides this touch
    return m, stop, tgt


def compute(df, sgn):
    k = U.key(df)
    b = U.base(df)
    em = U.ema_macd(df)
    bb, ee = U.segments(k)
    return _k(bb, ee, b["tod"], b["c"], b["h"], b["l"], em["e20"], em["macd"], em["cntp"], em["cntn"], b["vwap"],
              b["atr"], sgn, WINDOW[0], WINDOW[1])


def mask(df):
    m, s, t = compute(df, 1 if SIDE == "long" else -1)
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
