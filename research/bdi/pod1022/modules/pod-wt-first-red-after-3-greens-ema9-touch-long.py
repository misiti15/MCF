"""pod-wt-first-red-after-3-greens-ema9-touch-long - Ross Cameron first-red-candle 9-EMA bounce: after three green
new-high bars, the first red bar that touches and holds the 9 EMA (LONG).

Source: Warrior Trading blog, ASNS recap (Ross waited for green candles to be followed by the first red candle and
bought the bounce off the 9 moving average).
URL: https://www.warriortrading.com/?p=67831

VARIANT of bdi-vid-micropullback-long (1-minute micro-pullback / 9 EMA) and
pod-wt-micro-pullback-midday-reload-quiet-long. Stated changes: 5-minute frame, a single-bar trigger (the first red bar
after >= 3 green HOD bars), the low must touch EMA9 and the bar must close above it, and a 2R exit.

Rules (plain English), 5-minute bars, values from bars up to and including the decision bar:
  1. The 3 bars before the signal bar are green and each prints a new high of day.
  2. The signal bar is the first red bar after them; its low <= EMA9 + 0.05 x ATR14_5m and its close >= EMA9.
  3. Signal-bar volume < the mean volume of the 3 green bars.
  4. At the signal bar: close > session VWAP, fromOpen >= +2%, rvol_day >= 1.5.
  5. Signal-bar range (high - low) <= 1.0 x ATR14_5m (no wide flush).
  Entry: the first of the next 2 bars that breaks the red bar's high; the scorer fills at that bar's close, which must
  be above the red-bar high (a confirmed break). Window: entry bar close 10:00-14:30.
  Stop (GEOM S): red-bar low - 0.05 x ATR14_5m. Target: entry + 2R, else flat 15:55.
  Data notes: the frame has no 5m open; green / red use the previous 5m close as the open proxy (r24 bars). EMA9 is
  the session EMA of 5m closes seeded at 09:35. Modelling note: the source's exit on a 5m close below EMA9 and the
  45-minute time stop are not modelled (one stop / target per trade in the scorer). The random-entry control is the
  scorer's same-minute 'hold' control on the same universe. No tweak used.
Costs per config/default.yaml (applied by the scorer). Educational only - not financial advice."""
import sys
from pathlib import Path

import numba
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _r32_util as Z  # noqa: E402

SIDE = "long"
GEOM = "S"
WINDOW = (1000, 1430)
TARGET_R = 2.0
CONTEXT = []
LAYERS = ["3 green new-HOD bars", "first red bar touches EMA9 (+0.05 ATR5m) and closes >= EMA9",
          "red-bar volume < mean of the 3 greens", "close > VWAP, fromOpen >= 2, rvol_day >= 1.5",
          "red-bar range <= 1 ATR5m", "next 1-2 bars close above the red high", "stop red low - 0.05 ATR5m, 2R",
          "10:00-14:30"]
_ST = {}


@numba.njit(cache=False)
def _kern(b, e, tod, c, o, h, l, hod, vw, e9, a5, v, fo, rvc, w0, w1, tr):
    n = len(c)
    m = np.zeros(n, np.bool_)
    stop = np.full(n, np.nan)
    tgt = np.full(n, np.nan)
    for s in range(len(b)):
        i0, i1 = b[s], e[s]
        for i in range(i0 + 4, i1):
            if tod[i] < w0 or tod[i] > w1:
                continue
            for d in range(1, 3):
                j = i - d
                if j - 3 < i0:
                    break
                if d == 2 and c[i - 1] > h[j]:
                    break                           # bar j+1 already broke it: entry was that bar
                ok = True
                gv = 0.0
                for t in range(j - 3, j):
                    if not (c[t] > o[t] and h[t] >= hod[t] - 1e-9 * c[t]):
                        ok = False
                        break
                    gv += v[t]
                if not ok:
                    continue
                a = a5[j]
                if not (c[j] < o[j] and a > 0):
                    continue
                if not (l[j] <= e9[j] + 0.05 * a and c[j] >= e9[j]):
                    continue
                if not (v[j] < gv / 3.0):
                    continue
                if not (c[j] > vw[j] and fo[j] >= 2.0 and rvc[j] >= 1.5):
                    continue
                if not (h[j] - l[j] <= a):
                    continue
                if not (c[i] > h[j]):
                    continue
                sp = l[j] - 0.05 * a
                if not (c[i] > sp):
                    continue
                m[i] = True
                stop[i] = sp
                tgt[i] = c[i] + tr * (c[i] - sp)
                break
    return m, stop, tgt


def mask(df) -> np.ndarray:
    n = len(df)
    _ST.clear()
    if not n:
        return np.zeros(0, bool)
    B = Z.base(df)
    bb = Z.bars(df)
    b, e = Z.segments(Z.key(df))
    c = B["c"]
    with np.errstate(invalid="ignore"):
        a5 = Z.f(df, "atrPct") / 100 * c
    m, stop, tgt = _kern(b, e, B["tod"], c, bb["cprev"], B["h"], B["l"], B["hod"], B["vwap"], bb["e9"], a5, bb["v"],
                         Z.f(df, "fromOpen"), bb["rvc"], WINDOW[0], WINDOW[1], TARGET_R)
    _ST[id(df)] = (stop, tgt)
    return np.asarray(m, bool)


def _g(f, i, j):
    if id(f) not in _ST:
        mask(f)
    return float(_ST[id(f)][j][i])


def stop_price(f, i):
    return _g(f, i, 0)


def target_price(f, i, stop):
    return _g(f, i, 1)
