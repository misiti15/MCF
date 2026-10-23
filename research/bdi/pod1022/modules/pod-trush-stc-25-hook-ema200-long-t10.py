"""pod-trush-stc-25-hook-ema200-long-t10 - COMPANION (pre-declared): STC threshold 10 instead of 25.
(5-minute bars, LONG).

Source: Trading Rush YouTube channel; the strategy as listed in the unofficial 'Trading Rush Signals & Alerts'
TradingView script (STC signal crosses above 25 with price above the 200 EMA, 100-trade test, 1.5 R:R).
URL: https://www.tradingview.com/script/4gXXEI5Y-Trading-Rush-Signals-Alerts

NEW indicator family (no STC in the backlog, the generator or the pod modules).
Indicator: STC per symbol on continuous full-session 5m closes across days (09:35..15:55, previous open month as
warm-up): MACD = EMA23 - EMA50, then two passes of a 10-bar stochastic each smoothed with factor 0.5 (the standard
Schaff / TradingView formula). EMA200 on the same continuous 5m closes.
Rules (plain English, LONG):
  1. STC crosses up: <= 25 on the prior 5m bar and > 25 on this bar.
  2. Close > EMA200(5m) and EMA200 > its value 12 bars ago.
  3. spy_fo > -0.20% and breadth >= 0.45 (no broad sell-off).
  4. |close - session VWAP| <= 0.6 x atr_d (not over-extended); adv20 >= $20M (the default universe).
  Entry: bar close, 10:30-14:30. Stop (GEOM S): lowest low of the last 6 bars (this bar and the 5 before)
  - 0.05 x atr_d. Target: 1.5 x risk (the source's 1.5 R:R), else flat 15:55.
Pre-declared configurations (3): threshold 25 (this main), threshold 10 (-t10), and STC on 15m closes resampled from
the 5m bars (-15m; the cross is read on the 5m bar that completes the 15m bar). No tweak made.
Costs per config/default.yaml (scorer). Only closed bars up to the decision bar are used.
Educational only - not financial advice."""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import _r38_util as U  # noqa: E402

SIDE = "long"
GEOM = "S"
WINDOW = (1030, 1430)
CONTEXT = ["spy_fo", "breadth"]
THR = 10.0
TF = 5
LAYERS = ["STC(10,23,50) crosses above 25", "close > EMA200(5m), EMA200 rising over 12 bars",
          "spy_fo > -0.20, breadth >= 0.45", "|close - VWAP| <= 0.6 ATR", "10:30-14:30",
          "stop 6-bar low - 0.05 ATR, target 1.5R"]
_ST = {}


def _compute(df):
    n = len(df)
    if not n or "spy_fo" not in df or "breadth" not in df:
        z = np.full(n, np.nan)
        return np.zeros(n, bool), z, z
    b = U.base(df)
    x = U.stc_ema_rows(df)
    c, atr, tod = b["c"], b["atr"], b["tod"]
    s, sp = (x["stc"], x["stcp"]) if TF == 5 else (x["stc15"], x["stc15p"])
    with np.errstate(invalid="ignore"):
        m = (sp <= THR) & (s > THR)
        m &= (c > x["ema"]) & (x["ema"] > x["ema12"])
        m &= (U.f(df, "spy_fo") > -0.20) & (U.f(df, "breadth") >= 0.45)
        m &= np.abs(c - b["vwap"]) <= 0.6 * atr
        m &= (tod >= WINDOW[0]) & (tod <= WINDOW[1]) & (atr > 0)
        stop = x["lo6"] - 0.05 * atr
        tgt = c + 1.5 * (c - stop)
    return np.asarray(m, bool), stop, tgt


def mask(df):
    m, s, t = _compute(df)
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
