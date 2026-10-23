"""pod-of3-dalton-neutral-day-center-revert - Neutral day (both IB ends extended): fade the outer quarter back to the
day's centre in the afternoon. LONG side (the idea's weighted-first side); the SHORT mirror is scored separately as
pod-of3-dalton-neutral-day-center-revert-short.

Source: Dalton day-type taxonomy (neutral day: range extension on both sides of the IB, close in the centre) via the
LuxAlgo 'Day-type Taxonomy' concept page ('mid-range closes confirm balance'; 'rotational day types favour fading
the edges').
URL: https://www.luxalgo.com/library/concept/day-type-taxonomy.md

VARIANT of pod-of-ib-mid-rotation (requires NO IB extension, window from 10:35) and
pod-hart-serafini-midday-range-edge-fade (midday box edge). Stated change: a different day type (both IB ends
already broken = neutral day), a later window and the day midpoint as the target.
Rules (plain English, LONG; SHORT mirrors at the top):
  1. IB = 09:30-10:30 high / low (running HOD / LOD on the 10:30 bar). By the signal bar both the IB high and the IB
     low have been exceeded by >= 0.05 x atr_d.
  2. Day range 1.0-1.4 x IB width and <= 1.3 x atr_d; |spy_fo| <= 0.5%.
  3. Bar close 12:30-15:15 (the scorer clips entries at 15:00): close in the bottom 25% of the day range, >= 0.03 x
     atr_d above the LOD, no new LOD in the last 3 bars (LOD now == LOD 3 bars ago), volumeRatio <= 1.3.
  4. The bar closes above the prior bar's high and rsi5 < 45.
  Entry: close. Stop (GEOM S): LOD - 0.05 x atr_d. Target: day midpoint (HOD + LOD) / 2, taken only if >= 0.25 x
  atr_d away. Flat 15:55.
No tweak made. Costs per config/default.yaml (scorer). Only bars up to the decision bar are used.
Educational only - not financial advice."""
SIDE = "long"
GEOM = "S"
WINDOW = (1230, 1500)
CONTEXT = ["spy_fo"]
LAYERS = ["both IB ends extended >= 0.05 ATR", "range 1.0-1.4 x IB and <= 1.3 ATR, |spy_fo| <= 0.5",
          "close in outer 25%, >= 0.03 ATR off the extreme, no new extreme 3 bars, vr <= 1.3",
          "close beyond prior bar's high/low, rsi5 < 45 (> 55 short)", "stop extreme -/+ 0.05 ATR, target mid >= 0.25 ATR"]

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
    if not n or "spy_fo" not in df:
        return np.zeros(n, bool)
    b = U.base(df)
    k = U.key(df)
    c, atr, tod, hod, lod = b["c"], b["atr"], b["tod"], b["hod"], b["lod"]
    ibh = U.at_tod(hod, k, tod, 1030)
    ibl = U.at_tod(lod, k, tod, 1030)
    ibw = ibh - ibl
    rng = hod - lod
    mid = (hod + lod) / 2
    r5 = U.f(df, "rsi5")
    with np.errstate(invalid="ignore", divide="ignore"):
        m = (hod >= ibh + 0.05 * atr) & (lod <= ibl - 0.05 * atr) & (tod > 1030)
        m &= (rng >= 1.0 * ibw) & (rng <= 1.4 * ibw) & (rng <= 1.3 * atr) & (ibw > 0)
        m &= np.abs(U.f(df, "spy_fo")) <= 0.5
        m &= U.f(df, "volumeRatio") <= 1.3
        if SIDE == "long":
            m &= (c - lod <= 0.25 * rng) & (c - lod >= 0.03 * atr)
            m &= np.abs(lod - U.lag(lod, k, 3)) <= 1e-9 * c
            m &= (c > U.lag(b["h"], k)) & (r5 < 45)
            stop[:] = lod - 0.05 * atr
            tgt[:] = mid
            m &= (mid - c >= 0.25 * atr)
        else:
            m &= (hod - c <= 0.25 * rng) & (hod - c >= 0.03 * atr)
            m &= np.abs(hod - U.lag(hod, k, 3)) <= 1e-9 * c
            m &= (c < U.lag(b["l"], k)) & (r5 > 55)
            stop[:] = hod + 0.05 * atr
            tgt[:] = mid
            m &= (c - mid >= 0.25 * atr)
        m &= (tod >= WINDOW[0]) & (tod <= WINDOW[1]) & (atr > 0)
    return np.asarray(m, bool)
