"""pod-alvarez-nostop-etf-oversold-time-exit-long - Choppy-day ETF oversold dip, no strategy stop, time exit (Alvarez
exit rule; LONG).

Source: The Algorithmic Advantage ep 045 'Cesar Alvarez' (mean-reversion strategies did best without stops); Better
System Trader ep 130 / 133 'Building Mean Reversion trading strategies' with Cesar Alvarez.
URL: https://algoadvantage.substack.com/p/episode-045-cesar-alvarez-a-novel

VARIANT of pod-chop-etf-oversold-vwap-magnet-long. Stated change: exit logic only. Entry conditions are identical to
the parent for a clean exit comparison.

Rules (plain English, LONG). SYMBOLS: SPY, QQQ, IWM, DIA, XLF, XLK, XLE, XLV, XLI, XLY, XLP, XLU, SMH, XBI, KRE.
  1. Bar close 10:30-14:30.
  2. Choppy, balanced tape: |spy_fo| <= 0.40 and breadth 0.35-0.65.
  3. rsi5 <= 15.
  4. vwapDistPct <= -0.35.
  5. sma20_slope_pct >= -0.10.
  Entry: that bar's close; one trade per symbol per day. No strategy stop and no VWAP target: exit on the first
  5-minute close with rsi5 >= 60, or at 15:55; a disaster stop at entry - 1.0 x atr_d (risk control). R = 1.0 x atr_d
  (the disaster stop distance).
Harness limit (declared): the scorer cannot exit on an indicator. The scorer number is GEOM S with the disaster stop
only (hold to 15:55 unless the -1 ATR stop hits, R = atr_d). The rsi5 >= 60 exit is re-simulated post hoc by the r2_5
run from the scorer's trades (RSI(5) on the continuous 5-minute closes, same costs) and reported alongside, with bps
per trade. No tweak made. Costs per config/default.yaml.
Educational only - not financial advice."""
SIDE = "long"
GEOM = "S"
WINDOW = (1030, 1430)
SYMBOLS = ["SPY", "QQQ", "IWM", "DIA", "XLF", "XLK", "XLE", "XLV", "XLI", "XLY", "XLP", "XLU", "SMH", "XBI", "KRE"]
CONTEXT = ["spy_fo", "breadth"]
RSI_EXIT = 60
LAYERS = ["index / sector ETFs", "|spy_fo| <= 0.40", "breadth 0.35-0.65", "rsi5 <= 15", "vwapDistPct <= -0.35",
          "sma20_slope_pct >= -0.10", "disaster stop entry - 1.0 ATR, exit rsi5 >= 60 or 15:55", "10:30-14:30 ET"]

import numpy as np

_ST = {}


def _f(df, c):
    return df[c].to_numpy(float) if c in df else np.full(len(df), np.nan)


def stop_price(f, i):
    s = _ST.get(id(f))
    if s is None or len(s) != len(f):
        mask(f)
        s = _ST.get(id(f))
    return float(s[i])


def mask(df) -> np.ndarray:
    _ST.clear()
    z = np.zeros(len(df), dtype=bool)
    if not len(df) or "spy_fo" not in df or "breadth" not in df:
        _ST[id(df)] = np.full(len(df), np.nan)
        return z
    tod = df["tod"].to_numpy(np.int64)
    c, atr, vd = _f(df, "close"), _f(df, "atr_d"), _f(df, "vwapDistPct")
    br = _f(df, "breadth")
    with np.errstate(invalid="ignore", divide="ignore"):
        m = np.isin(df["symbol"].astype(str).to_numpy(), SYMBOLS)
        m &= np.abs(_f(df, "spy_fo")) <= 0.40
        m &= (br >= 0.35) & (br <= 0.65)
        m &= _f(df, "rsi5") <= 15
        m &= vd <= -0.35
        m &= _f(df, "sma20_slope_pct") >= -0.10
        m &= (tod >= WINDOW[0]) & (tod <= WINDOW[1])
        stop = c - 1.0 * atr
        m &= stop < c
    _ST[id(df)] = stop
    return np.asarray(m, dtype=bool)
