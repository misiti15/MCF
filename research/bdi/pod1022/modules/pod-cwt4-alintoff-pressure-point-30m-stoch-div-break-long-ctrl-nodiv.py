"""pod-cwt4-alintoff-pressure-point-30m-stoch-div-break-long-ctrl-nodiv - CONTROL arm of the Alintoff pressure-point module (same box breakouts, no divergence condition).
Same rules as the main module below; only NEED_DIV = False differs.

Source: Chat With Traders ep 117, Larry Alintoff ('Pressure point: consolidation breakout with oscillator divergence';
moves that used to take weeks now take hours; test on 30-min bars intraday). URL: https://chatwithtraders.com/117

VARIANT of pod-velez-narrow-state-break (compression only) and pod-bbt-falling-wedge-div-quiet-long (wedge
structure). Stated change: a flat or ascending box plus a positive stochastic divergence at the second box-low test,
on 30-minute structure with a 5-minute trigger.

Rules (plain English). 30-minute bars are built from the continuous full-session 5-minute bars (09:30-10:00, ...,
15:30-16:00; prior session included); only 30-minute bars COMPLETED by the decision bar's close are used.
  0. Universe: D-1 close > $10 and D-1 close > daily SMA50 (completed days).
  1. Box: the last 8 completed 30-minute bars (spanning the prior and current session) have high - low <= 0.6 x the
     mean 30-minute range (last 20 bars) x 8, and lows flat or rising (lowest low of the last 4 bars >= lowest low of
     the first 4 bars - 0.1 x box height).
  2. Two tests of the box low (bar low within 0.1 x box height of it), the first and the last test at least 2 bars
     apart. Stochastic %K(14,3) on 30-minute bars at the last test >= %K at the first test + 10 (positive divergence).
  3. Trigger: a 5-minute close above box high + 0.02 x atr_d (the previous 5m close was not), bar volumeRatio >= 1.2,
     bar close 11:00-15:00 ET.
  Entry: the trigger close (= next 5m open). Stop (GEOM S): box midpoint. Target: box high + 1.0 x box height
  (measured move), else 15:55. One per symbol per day (scorer). Costs per config/default.yaml (scorer).
Control (separate module ...-ctrl-nodiv): the same box breakouts without the divergence condition.
No tweak used. Only bars up to the decision bar are used.
Educational only - not financial advice."""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _r31_util as U  # noqa: E402

SIDE = "long"
GEOM = "S"
WINDOW = (1100, 1500)
NEED_DIV = False
LAYERS = ["D-1 close > $10 and > SMA50", "8 x 30m box <= 0.6 x avg30 x 8, lows flat/rising",
          "2 box-low tests, %K(30m) higher by >= 10", "5m close > box high + 0.02 ATR, volumeRatio >= 1.2",
          "stop box mid, target box high + height", "11:00-15:00 ET"]
_ST = {}


def compute(df):
    b = U.base(df)
    k = U.key(df)
    dd = U.U.map_daily(df, k, ["c1", "sma501"])
    bx = U.box30(df, 8, NEED_DIV)
    c, atr = b["c"], b["atr"]
    hi, lo = bx["bhi"], bx["blo"]
    with np.errstate(invalid="ignore"):
        lvl = hi + 0.02 * atr
        m = (bx["bok"] == 1) & (c > lvl) & ~(U.lag(c, k, 1) > lvl)
        m &= U.f(df, "volumeRatio") >= 1.2
        m &= (dd["c1"] > 10) & (dd["c1"] > dd["sma501"])
        m &= (b["tod"] >= WINDOW[0]) & (b["tod"] <= WINDOW[1])
        stop = (hi + lo) / 2
        tgt = hi + (hi - lo)
        m &= (stop < c) & (tgt > c)
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
