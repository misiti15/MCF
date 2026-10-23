"""pod-of3-dalton-rf-balance-lowerhalf-long - Rotation-factor up-bias on a quiet balance day: buy the lower half of
the range (LONG).

Source: James Dalton, Mind Over Markets (rotation factor, day-timeframe attempted direction), via the LuxAlgo
'Rotation Factor' concept page and the TradingView 'Rotational Factor Calculation' script.
URL: https://www.luxalgo.com/library/concept/rotation-factor.md

NEW feature family (30-minute bracket rotation factor). Differs from pod-of-ib-mid-rotation (no IB-midpoint cross;
entry gated by RF bias) and pod-dalton-quiet-poc-revert (anchor = range midpoint / VWAP, gate = RF).
Rotation factor (RF): 30-min brackets 09:30-10:00, 10:00-10:30, ... built from today's 5m highs / lows (bracket 0 from
the running HOD / LOD on the 10:00 bar, because the frame starts at 09:50). For each completed bracket after the first:
+1 if its high > the prior bracket's high, -1 if lower; +1 if its low > the prior bracket's low, -1 if lower. RF = the
sum over all completed brackets (a bracket counts once its last 5m bar has closed).
Rules (plain English, LONG), bar close 12:00-14:30:
  1. Day range so far (HOD - LOD) <= 0.8 x atr_d and |spy_fo| <= 0.5.
  2. RF of the completed brackets >= +4, and no new HOD in the last 6 bars (running HOD now == HOD 6 bars ago).
  3. Close in the lower 35% of the day range and >= 0.05 x atr_d above the LOD.
  4. The bar closes above the prior bar's high, and rsi5 > rsi5 one bar ago.
  Entry: close. Stop (GEOM S): LOD - 0.05 x atr_d. Target: max(day midpoint (HOD + LOD) / 2, session VWAP); the trade
  is taken only if target - entry >= 1.0 x (entry - stop) and >= 0.25 x atr_d (cost floor). Flat 15:55.
No tweak made. Costs per config/default.yaml (scorer). Only bars up to the decision bar are used.
Educational only - not financial advice."""
SIDE = "long"
GEOM = "S"
WINDOW = (1200, 1430)
CONTEXT = ["spy_fo"]
LAYERS = ["day range <= 0.8 ATR, |spy_fo| <= 0.5", "RF >= +4, no new HOD in 6 bars",
          "close in lower 35% of range, >= 0.05 ATR above LOD", "close > prior high, rsi5 rising",
          "stop LOD - 0.05 ATR, target max(mid, VWAP) >= 1R and >= 0.25 ATR"]

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
    c, atr, tod = b["c"], b["atr"], b["tod"]
    nb, R = U.rf_contrib(df, k, b)
    rf = U.rf_total(nb, R)
    rng = b["hod"] - b["lod"]
    r5 = U.f(df, "rsi5")
    with np.errstate(invalid="ignore", divide="ignore"):
        m = (rng <= 0.8 * atr) & (np.abs(U.f(df, "spy_fo")) <= 0.5)
        m &= (rf >= 4) & (np.abs(b["hod"] - U.lag(b["hod"], k, 6)) <= 1e-9 * c)
        m &= ((c - b["lod"]) <= 0.35 * rng) & ((c - b["lod"]) >= 0.05 * atr)
        m &= (c > U.lag(b["h"], k)) & (r5 > U.lag(r5, k))
        stop[:] = b["lod"] - 0.05 * atr
        tgt[:] = np.maximum((b["hod"] + b["lod"]) / 2, b["vwap"])
        m &= ((tgt - c) >= 1.0 * (c - stop)) & ((tgt - c) >= 0.25 * atr) & (stop < c)
        m &= (tod >= WINDOW[0]) & (tod <= WINDOW[1]) & (atr > 0)
    return np.asarray(m, bool)
