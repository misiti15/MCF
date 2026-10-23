"""pod-connors-hourly-rsi2-uptrend-index-long - Hourly RSI(2) dip in a daily uptrend, index ETFs, flat by the close
(LONG).

Source: Quantified Strategies, 'What is the best RSI oversold level? (tested 1-50)'; Backtrex, 'Does the RSI(2)
strategy work on the S&P 500?' (Connors RSI(2) buy-the-dip above the 200-day; suggests shorter candles for more
trades).
URL: https://backtrex.com/en/backtests/connors-rsi-2-sp-500

VARIANT of 'RSI(2)/IBS mean reversion on intraday bars' (setups_research). Stated change: 60-minute bars built from
5-minute data (hours ending 10:30, 11:30, ..., 15:30, then a last half hour ending at the 15:55 bar), a two-level daily
trend gate and an exit at the hourly SMA5. Index ETFs only.

Rules (plain English, LONG), SYMBOLS SPY, QQQ, IWM:
  1. Daily trend: D-1 close > daily SMA200 and > daily SMA20 (completed days only).
  2. RSI(2) (Wilder) of 60-minute closes, continuous across sessions (prior days' hourly bars included), is < 10 at
     one of the hourly closes 10:30, 11:30, 12:30, 13:30, 14:30.
  3. That hourly close is at least 0.3 x daily ATR14 below the session high so far (a real dip).
  Entry: at that hourly close (the 5-min bar ending at the hour). One entry per symbol per day (the scorer's first).
  Stop (GEOM S): entry - 0.5 x daily ATR14. Exit: the hourly SMA5 (mean of the last 5 completed hourly closes at the
  signal), else flat at 15:55.
Harness deviations (stated): (a) the source exit is the first 5-min CLOSE above the hourly SMA5, re-evaluated every
hour; the scorer only supports a fixed limit, so the target is the SMA5 value at the signal, filled on touch
(slightly optimistic vs a close-above rule, and it ignores later SMA5 updates); (b) the open daily history restarts on
2025-03-03 (the locked block is never bridged), so SMA200 uses min 100 sessions and the gate is live from about late
July 2025; (c) the 16:00 bar is not in the history, so the last hour of each day ends at the 15:55 close. No tweak
made. Costs per config/default.yaml. Educational only - not financial advice."""
import numpy as np

import _r212_util as U

SIDE = "long"
GEOM = "S"
WINDOW = (1030, 1430)
SYMBOLS = ["SPY", "QQQ", "IWM"]
HOURS = (1030, 1130, 1230, 1330, 1430)
LAYERS = ["D-1 close > SMA200 and > SMA20", "hourly RSI(2) < 10 at 10:30-14:30 hourly closes",
          "close <= HOD - 0.3 ATR", "stop entry - 0.5 ATR, target hourly SMA5, flat 15:55"]
_ST = {}


def _compute(df):
    n = len(df)
    b = U.base(df)
    k = U.key(df)
    tod, c = b["tod"], b["c"]
    dx = U.map_dx(df, k, ["c1", "sma20_1", "sma200_1"])
    h = U.hourly(df)
    if h is None:
        return np.zeros(n, bool), np.full(n, np.nan), np.full(n, np.nan)
    hr = U.CB.map_rows(df, h, ["rsi2h", "sma5h"])
    with np.errstate(invalid="ignore"):
        m = (dx["c1"] > dx["sma200_1"]) & (dx["c1"] > dx["sma20_1"])        # (1)
        m &= np.isin(tod, HOURS) & (hr["rsi2h"] < 10)                       # (2)
        m &= c <= b["hod"] - 0.3 * b["atr"]                                 # (3)
        sp = c - 0.5 * b["atr"]
        tg = hr["sma5h"]
        m &= tg > c
    return np.asarray(m, bool), sp, tg


def mask(df) -> np.ndarray:
    try:
        m, sp, tg = _compute(df)
    except (KeyError, FileNotFoundError):
        m, sp, tg = np.zeros(len(df), bool), np.full(len(df), np.nan), np.full(len(df), np.nan)
    _ST.clear()
    _ST[id(df)] = (sp, tg)
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
