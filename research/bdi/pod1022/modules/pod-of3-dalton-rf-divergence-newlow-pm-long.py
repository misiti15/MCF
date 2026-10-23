"""pod-of3-dalton-rf-divergence-newlow-pm-long - Afternoon new low with a non-negative rotation factor (RF divergence)
reversal (LONG).

Source: Dalton rotation factor used as a divergence check against price (LuxAlgo 'Rotation Factor' concept:
'divergence check against price direction'); TradingView 'Rotational Factor Calculation' script.
URL: https://www.tradingview.com/script/LW2PAE6k-Rotational-Factor-Calculation

VARIANT of pod-three-push-deceleration-low-long and the bull_div lab uses: the divergence is structural (30-min
bracket RF) instead of RSI or swing deceleration. RF brackets as in pod-of3-dalton-rf-balance-lowerhalf-long
(bracket 0 = 09:30-10:00 from the running HOD / LOD on the 10:00 bar; a bracket counts once its last bar closed).
Rules (plain English, LONG), bar close 12:30-15:00:
  1. The new-low bar (this bar or the prior bar) set a new running LOD, that LOD is still the LOD now, and it is
     <= 0.20 x atr_d below the LOD of 12 bars before the new-low bar (a shallow new low, not a flush).
  2. RF summed over the last 4 completed 30-min brackets (each vs its predecessor) >= 0, and fromOpen < 0.
  3. Day range <= 1.1 x atr_d and spy_fo >= -0.4.
  4. The new-low bar's volumeRatio <= 1.3 (no liquidation).
  5. Entry: this bar closes above the prior bar's high (within 2 bars of the new low: the new-low bar is this bar or
     the prior one; the scorer takes the first such bar of the day).
  Stop (GEOM S): the new LOD - 0.05 x atr_d. Target: session VWAP; skipped if VWAP < 0.25 x atr_d above entry.
  Flat 15:55.
No tweak made. Costs per config/default.yaml (scorer). Only bars up to the decision bar are used.
Educational only - not financial advice."""
SIDE = "long"
GEOM = "S"
WINDOW = (1230, 1500)
CONTEXT = ["spy_fo"]
LAYERS = ["new LOD this/prior bar, <= 0.2 ATR below the LOD 12 bars earlier", "RF(last 4 brackets) >= 0, fromOpen < 0",
          "day range <= 1.1 ATR, spy_fo >= -0.4", "new-low bar volumeRatio <= 1.3", "close > prior high",
          "stop LOD - 0.05 ATR, target VWAP >= 0.25 ATR"]

import sys
from pathlib import Path

import numpy as np

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
    if not n or "spy_fo" not in df:
        return np.zeros(n, bool)
    b = U.base(df)
    k = U.key(df)
    c, atr, tod, lod = b["c"], b["atr"], b["tod"], b["lod"]
    nb, R = U.rf_contrib(df, k, b)
    rf4 = U.rf_last(nb, R, 4)
    vr = U.f(df, "volumeRatio")
    eps = 1e-9 * np.where(np.isfinite(c), c, 0)
    lod1, lod2 = U.lag(lod, k, 1), U.lag(lod, k, 2)
    with np.errstate(invalid="ignore"):
        # new-low bar = this bar
        a0 = (lod < lod1 - eps) & (lod >= U.lag(lod, k, 12) - 0.20 * atr) & (vr <= 1.3)
        # new-low bar = prior bar, LOD unchanged since
        a1 = (lod1 < lod2 - eps) & (np.abs(lod - lod1) <= eps) & (lod1 >= U.lag(lod, k, 13) - 0.20 * atr) \
            & (U.lag(vr, k) <= 1.3)
        m = a0 | a1
        m &= (rf4 >= 0) & (U.f(df, "fromOpen") < 0)
        m &= ((b["hod"] - lod) <= 1.1 * atr) & (U.f(df, "spy_fo") >= -0.4)
        m &= c > U.lag(b["h"], k)
        stop[:] = lod - 0.05 * atr
        tgt[:] = b["vwap"]
        m &= ((tgt - c) >= 0.25 * atr) & (stop < c)
        m &= (tod >= WINDOW[0]) & (tod <= WINDOW[1]) & (atr > 0)
    return np.asarray(m, bool)
