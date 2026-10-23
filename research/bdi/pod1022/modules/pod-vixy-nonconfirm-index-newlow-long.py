"""pod-vixy-nonconfirm-index-newlow-long - Volatility non-confirmation: the index makes a new session low but the VIX
ETF does not make a new high (LONG on SPY / QQQ).

Source: MoneyShow, day-trading divergence article (SPY 5-min divergences vs indicators / TICK); StockCharts
ChartWatchers, 'VIX turns up, S&P turns down'.
URL: https://moneyshow.com/articles/daytraders-21606

VARIANT of pod-raschke-blindfold-breadth-div (and a sibling of pod-vxx-lower-high-spy-newlow-div-long). Stated
change: the non-confirmation comes from the volatility ETF's 5-min high vs its session high, checked on the same bar,
with no follow-through bar required. VIXY is not in the history; UVXY (named by the source idea as the alternative)
is used; its rows come from the open history frames of the same month (never the locked block).

Rules (plain English, LONG). SYMBOLS: SPY, QQQ (each on its own bars).
  1. The traded ETF's daily close yesterday > its daily SMA50 (lib.daily(), completed days).
  2. Bar closes 10:30-14:30 ET and its low is a new session low: low < the running low of day as of the previous bar
     x (1 - 0.03%) (the running low includes 09:30-09:45).
  3. On the same bar, UVXY's high is >= 0.5% below UVXY's session high so far (vol fails to confirm).
  4. The bar closes in the upper 50% of its range.
  Entry: that bar's close. Stop (GEOM S): bar low - 0.1 x 5-min ATR(14) (atrPct x close). Target: the session VWAP;
  if VWAP is < 1R above the entry, the target is entry + 1.5R. Flat 15:55. One trade per symbol-day (scorer).
No tweak made. Costs per config/default.yaml (scorer). Only bars up to the decision bar are used.
Educational only - not financial advice."""
SIDE = "long"
GEOM = "S"
WINDOW = (1030, 1430)
SYMBOLS = ["SPY", "QQQ"]
LAYERS = ["D-1 close > SMA50", "new LOD >= 0.03% below the prior LOD, 10:30-14:30",
          "UVXY high <= UVXY session high x (1 - 0.5%)", "close in the upper 50% of the bar",
          "stop bar low - 0.1 x 5m ATR, target VWAP or 1.5R if VWAP < 1R"]

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
    b = U.base(df)
    k = U.key(df)
    tod, c, h, l = b["tod"], b["c"], b["h"], b["l"]
    d = U.map_daily(df, k, ["c1", "sma50_1"])
    v = U.vxx_rows(df, "UVXY")
    if v is None:
        return z
    vv = U.map_dt(df, v, ["vh", "vhod"])
    lodp = U.lag(b["lod"], k, 1)
    with np.errstate(invalid="ignore"):
        m = d["c1"] > d["sma50_1"]                                       # (1)
        m &= (tod >= 1030) & (tod <= 1430) & (l < lodp * (1 - 0.0003))    # (2)
        m &= vv["vh"] <= vv["vhod"] * (1 - 0.005)                          # (3)
        m &= (c - l) >= 0.5 * (h - l)                                      # (4)
        m &= h > l
        stop[:] = l - 0.1 * b["atr5"]
        r = c - stop
        vw = b["vwap"]
        tgt[:] = np.where(vw - c >= r, vw, c + 1.5 * r)
        m &= (stop < c) & (tgt > c)
    _ST[id(df)] = (stop, tgt)
    return np.asarray(m, bool)
