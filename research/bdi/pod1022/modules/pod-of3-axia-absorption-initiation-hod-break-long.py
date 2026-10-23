"""pod-of3-axia-absorption-initiation-hod-break-long - Absorption at the high, then initiation: buy the HOD break after
a high-volume narrow bar that does not drop (LONG).

Source: Axia Futures YouTube 'Absorption vs. Initiation' / 'Absorption In The Footprint' (passive sellers absorbed at
a level, then aggressive buyers initiate) and 'Absorption Creating A Sell Opportunity' (mirror).
URL: https://www.youtube.com/watch?v=OZ9krGm1g6o

VARIANT of pod-of-absorption-bar-level (reversal FROM the level after absorption). Stated change: the absorption bar
sits under the HOD on an up day and the trade is the continuation THROUGH the HOD once buyers initiate.
Rules (plain English, LONG):
  1. Up day (checked on the entry bar): close - today's open >= 0.5 x atr_d (fromOpen >= 0.5 x atr_d / close x 100),
     spy_fo >= 0, breadth >= 0.5.
  2. Absorption bar A, bar close 10:15-14:15: its high is within 0.10 x atr_d of the HOD (as of A's close),
     volumeRatio >= 1.8, range <= 0.6 x the 5m ATR (atrPct x close), close in the upper half of its range,
     upper_wick <= 0.4.
  3. Within the next 3 bars, the FIRST close above the HOD as of A is the entry bar, and it must show initiation:
     flow3 >= +0.3. No close below A's low before it (bars between A and the entry).
  Entry: that close. Stop (GEOM S): A's low - 0.05 x atr_d. Target: entry + 1.5 x the stop distance, taken only if
  that is >= 0.25 x atr_d. Flat 15:55. Window: entry bar close 10:20-14:30.
Reading declared up front: 'first close above the HOD ... with flow3 >= +0.3' is read as 'the first close above the
HOD must itself have flow3 >= +0.3' (no second chance). No tweak made. Costs per config/default.yaml (scorer).
Educational only - not financial advice."""
SIDE = "long"
GEOM = "S"
WINDOW = (1020, 1430)
CONTEXT = ["spy_fo", "breadth"]
LAYERS = ["up day >= 0.5 ATR from open, spy_fo >= 0, breadth >= 0.5",
          "absorption bar A near HOD: vr >= 1.8, range <= 0.6 x 5m ATR, upper-half close, upper wick <= 0.4",
          "first close above HOD(A) within 3 bars, flow3 >= 0.3, no close below A low",
          "stop A low - 0.05 ATR, target 1.5x risk (>= 0.25 ATR)"]

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _r210_util as U  # noqa: E402

_ST = {}


def _get(f, i, j):
    s = _ST.get(id(f))
    if s is None or len(s[0]) != len(f):
        mask(f)
        s = _ST.get(id(f))
    return float(s[j][i])


def stop_price(f, i):
    return _get(f, i, 0)


def target_price(f, i, stop):
    return _get(f, i, 1)


def mask(df) -> np.ndarray:
    _ST.clear()
    n = len(df)
    stop, tgt = np.full(n, np.nan), np.full(n, np.nan)
    _ST[id(df)] = (stop, tgt)
    if not n or "spy_fo" not in df or "breadth" not in df:
        return np.zeros(n, bool)
    b = U.base(df)
    k = U.key(df)
    c, h, l, atr, tod, hod = b["c"], b["h"], b["l"], b["atr"], b["tod"], b["hod"]
    rng = h - l
    with np.errstate(invalid="ignore", divide="ignore"):
        isA = (hod - h <= 0.10 * atr) & (U.f(df, "volumeRatio") >= 1.8) & (rng <= 0.6 * b["atr5"]) & (rng > 0)
        isA &= (c - l >= 0.5 * rng) & (U.f(df, "upper_wick") <= 0.4) & (tod >= 1015) & (tod <= 1415)
        sig = np.zeros(n, bool)
        sl = np.full(n, np.nan)
        for j in (1, 2, 3):                     # A = j bars back
            aA = U.lag(isA.astype(float), k, j) == 1
            hA = U.lag(hod, k, j)
            lA = U.lag(l, k, j)
            ok = aA & (c > hA)
            for q in range(1, j):               # bars between A and now: no close above HOD(A), none below A low
                cq = U.lag(c, k, q)
                ok &= (cq <= hA) & (cq >= lA)
            new = ok & ~sig
            sl = np.where(new, lA, sl)          # nearest A wins (j = 1 first)
            sig |= ok
        m = sig & (U.f(df, "flow3") >= 0.3)
        m &= (c - b["opn"] >= 0.5 * atr) & (U.f(df, "spy_fo") >= 0) & (U.f(df, "breadth") >= 0.5)
        stop[:] = sl - 0.05 * atr
        risk = c - stop
        tgt[:] = c + 1.5 * risk
        m &= (risk > 0) & (1.5 * risk >= 0.25 * atr)
        m &= (tod >= WINDOW[0]) & (tod <= WINDOW[1]) & (atr > 0)
    return np.asarray(m, bool)
