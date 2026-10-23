"""pod-of3-dalton-rf-trend-bracket-low-pullback-long - Strong rotation-factor up-day: buy the pullback to the prior
30-min bracket low (LONG).

Source: Dalton rotation factor as a continuation filter (LuxAlgo 'Rotation Factor': 'strong rotation plus range
extension supports continuation'; trend days 'demand joining pullbacks').
URL: https://www.luxalgo.com/library/concept/rotation-factor.md

VARIANT of pod-breadth-trendday-index-pullback-long and pod-raschke-holygrail-adx-ema20 (trend gate = breadth / ADX,
pullback to an EMA). Stated change: the trend gate is the 30-min bracket RF and the pullback zone is the low of the
most recent completed 30-min bracket (TPO structure), not an EMA / VWAP.
Rotation factor (as in pod-of3-dalton-rf-balance-lowerhalf-long, _r29_util): brackets 09:30-10:00, 10:00-10:30, ...;
for each completed bracket after the first, +1 / -1 for a higher / lower high and +1 / -1 for a higher / lower low
vs the prior bracket; RF = the sum over completed brackets (a bracket counts once its last 5m bar has closed).
Rules (plain English, LONG), bar close 11:00-14:30:
  1. RF of the completed brackets >= +6, and at least one completed bracket after the IB (10:30+) made a high above
     the IB high (09:30-10:30).
  2. Close > session VWAP, breadth >= 0.55.
  3. The bar's low is within 0.08 x atr_d above, or at most 0.05 x atr_d below, the low of the most recent completed
     30-min bracket (the last bracket that closed BEFORE this bar's own bracket), and volumeRatio <= 1.0.
  4. The bar closes in its upper half and above that bracket low.
  Entry: close. Stop (GEOM S): bracket low - 0.12 x atr_d. Target: HOD + 0.25 x atr_d. Flat 15:55.
No tweak made. Costs per config/default.yaml (scorer). Only bars up to the decision bar are used.
Educational only - not financial advice."""
SIDE = "long"
GEOM = "S"
WINDOW = (1100, 1430)
CONTEXT = ["breadth"]
LAYERS = ["RF >= +6 with a post-IB bracket above the IB high", "close > VWAP, breadth >= 0.55",
          "low within +0.08 / -0.05 ATR of the last completed bracket low, vr <= 1.0",
          "upper-half close above that low", "stop bracket low - 0.12 ATR, target HOD + 0.25 ATR"]

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _r29_util as U  # noqa: E402

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
    if not n or "breadth" not in df:
        return np.zeros(n, bool)
    b = U.base(df)
    k = U.key(df)
    c, h, l, atr, tod, hod = b["c"], b["h"], b["l"], b["atr"], b["tod"], b["hod"]
    nb, R = U.rf_contrib(df, k, b)
    rf = U.rf_total(nb, R)
    mn = U.minutes(tod)
    bidx = (mn - 1) // 30
    ibh = U.at_tod(hod, k, tod, 1030)
    # running low / high within each bracket, recorded on the bracket's last bar, then forward-filled per day
    t = pd.DataFrame({"k": k, "j": bidx, "l": l, "h": h})
    g = t.groupby(["k", "j"], sort=False)
    rl = g["l"].cummin().to_numpy(float)
    rh = g["h"].cummax().to_numpy(float)
    end = (mn % 30) == 0
    lo0 = U.at_tod(b["lod"], k, tod, 1000)                 # bracket 0 low (09:30-10:00) = LOD on the 10:00 bar
    rl = np.where(bidx == 0, lo0, rl)
    bl = pd.Series(np.where(end, rl, np.nan)).groupby(k).ffill().to_numpy(float)
    bh_end = np.where(end & (bidx >= 2), rh, np.nan)        # post-IB bracket highs at their completion
    above = pd.Series((bh_end > ibh).astype(float)).where(end & (bidx >= 2)).groupby(k).cummax()
    above = above.groupby(k).ffill().to_numpy(float)
    blp = U.lag(bl, k)                                       # last bracket completed BEFORE this bar's bracket
    abp = U.lag(above, k)
    # on a bar that is not a bracket end, lag(bl) equals bl of the previous completed bracket too
    with np.errstate(invalid="ignore"):
        m = (rf >= 6) & (abp == 1)
        m &= (c > b["vwap"]) & (U.f(df, "breadth") >= 0.55)
        m &= (l <= blp + 0.08 * atr) & (l >= blp - 0.05 * atr) & (U.f(df, "volumeRatio") <= 1.0)
        m &= (c - l >= 0.5 * (h - l)) & (c > blp)
        stop[:] = blp - 0.12 * atr
        tgt[:] = hod + 0.25 * atr
        m &= (stop < c) & (tgt > c)
        m &= (tod >= WINDOW[0]) & (tod <= WINDOW[1]) & (atr > 0)
    return np.asarray(m, bool)
