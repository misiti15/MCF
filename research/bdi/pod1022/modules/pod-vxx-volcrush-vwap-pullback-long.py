"""pod-vxx-volcrush-vwap-pullback-long - Vol-crush day VWAP pullback (positive-gamma / quiet tape proxy, LONG ETFs).

Source: SpotGamma 'Nomura's McElligott explains... gamma gravity pins equities, intraday movement is squelched';
FlashAlpha SPY GEX guide (positive gamma: compressed, mean-reverting, dealers buy dips). VXX falling is the free
proxy for that regime.
URL: https://spotgamma.com/nomuras-mcelligott-explains-the-perfect-virtuous-feedback-loop-as-gamma-gravity-pins-equities-intraday-movement-is-squelched/

VARIANT of pod-bbt-orb-vwap-pullback-atr-room-long. Stated change: a volatility-ETN regime gate (vol-crush day)
replaces the opening-range condition, and the window is midday / afternoon.

Rules (plain English, LONG). SYMBOLS: SPY, QQQ, IWM, DIA + sector ETFs (XLF, XLK, XLE, XLV, XLI, XLY, XLP, XLU, XLB,
XLRE, XLC, SMH, XBI, KRE).
  1. On the signal bar, VXX fromOpen <= -2.5% and VXX closes below its session VWAP (VXX rows of the same bar).
  2. The traded ETF is up >= +0.2% from its open and its day range so far (HOD - LOD) <= 0.9 x atr_d.
  3. Bar close 11:00-14:45: the bar's low is within 0.10% above session VWAP or dips below it by at most 0.15%
     (vwap x (1 - 0.0015) <= low <= vwap x (1 + 0.0010)), the bar closes above VWAP, and rsi5 <= 45 on that bar or
     the bar before.
  Entry: that bar's close. Stop (GEOM S): VWAP - 0.25 x atr_d. Target: HOD so far; otherwise flat 15:55.
No tweak made. Costs per config/default.yaml (scorer). Only bars up to the decision bar are used.
Educational only - not financial advice."""
SIDE = "long"
GEOM = "S"
WINDOW = (1100, 1445)
SYMBOLS = ["SPY", "QQQ", "IWM", "DIA", "XLF", "XLK", "XLE", "XLV", "XLI", "XLY", "XLP", "XLU", "XLB", "XLRE", "XLC",
           "SMH", "XBI", "KRE"]
LAYERS = ["VXX fromOpen <= -2.5% and below its VWAP", "fromOpen >= 0.2%", "HOD - LOD <= 0.9 ATR",
          "low tags VWAP (-0.15% .. +0.10%), close > VWAP", "rsi5 <= 45 on this or the prior bar",
          "stop VWAP - 0.25 ATR, target HOD", "11:00-14:45 ET"]

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _r25_util as U  # noqa: E402

_ST = {}


def _stash(f, i, j):
    s = _ST.get(id(f))
    if s is None or len(s[0]) != len(f):
        mask(f)
        s = _ST.get(id(f))
    return float(s[j][i]) if s is not None else float("nan")


def stop_price(f, i):
    return _stash(f, i, 0)


def target_price(f, i, stop):
    return _stash(f, i, 1)


def mask(df) -> np.ndarray:
    _ST.clear()
    n = len(df)
    z = np.zeros(n, bool)
    stop, tgt = np.full(n, np.nan), np.full(n, np.nan)
    _ST[id(df)] = (stop, tgt)
    if not n:
        return z
    v = U.vxx_rows(df)
    if v is None:
        return z
    vx = U.map_dt(df, v, ["vfo", "vvd"])
    b = U.base(df)
    k = U.key(df)
    c, l, atr, vwap, tod = b["c"], b["l"], b["atr"], b["vwap"], b["tod"]
    r5 = U.f(df, "rsi5")
    with np.errstate(invalid="ignore"):
        m = (vx["vfo"] <= -2.5) & (vx["vvd"] < 0)                                   # (1)
        m &= U.f(df, "fromOpen") >= 0.2                                             # (2)
        m &= (b["hod"] - b["lod"]) <= 0.9 * atr
        m &= (l >= vwap * (1 - 0.0015)) & (l <= vwap * (1 + 0.0010)) & (c > vwap)   # (3)
        m &= (r5 <= 45) | (U.lag(r5, k, 1) <= 45)
        m &= (tod >= 1100) & (tod <= 1445)
        stop[:] = vwap - 0.25 * atr
        tgt[:] = b["hod"]
        m &= (stop < c) & (tgt > c)
    _ST[id(df)] = (stop, tgt)
    return np.asarray(m, bool)
