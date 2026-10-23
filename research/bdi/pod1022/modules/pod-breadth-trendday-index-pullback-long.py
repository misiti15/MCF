"""pod-breadth-trendday-index-pullback-long - Breadth-confirmed trend day: buy SPY/QQQ pullbacks that hold VWAP while
breadth holds (LONG).

Source: NexusFi Academy 'Trading with Market Internals' and 'NYSE TICK Index for Futures Traders'.
URL: https://nexusfi.com/a/strategies/trading-with-market-internals

VARIANT of bdi-tg-p-pullback-vwap-long (failed: not selective), the LD breadth-turn index dips (LD1-LD8) and the
bdi-rg-g1 breadth gates (used only as filters there). Stated change: a decision-time breadth trend-day gate on index
ETFs, and breadth must hold during the pullback (TICK-not-negative proxy).

Rules (plain English), SYMBOLS SPY, QQQ; breadth = share of the universe above its own VWAP (ADD/TICK proxy):
  1. Trend day by breadth: breadth >= 0.70 on the 10:30 bar and >= 0.60 on every bar from 10:30 to the decision bar.
  2. SPY closed above its session VWAP on every bar from 10:00 to the decision bar (SPY's own rows).
  3. Pullback (touch bar, at or after 10:30): low <= EMA9 or low within 0.05% of VWAP, close above VWAP, and
     breadth >= 0.50 on that bar.
  4. Trigger: the first bar after a touch that closes above EMA9 and above the prior bar's high (the scorer takes
     the first such bar of the day).
  Entry: that close, bar close 10:30-14:30. Stop (GEOM S): VWAP - 0.10 x atr_d (VWAP on the entry bar). Target:
  HOD + 0.10 x atr_d (HOD as of the entry bar), else flat 15:55.
EMA9 = 5-minute EMA(9) of close, run continuously per symbol over the frame (the 09:35-09:45 bars are absent from the
history frames, a small deviation). No tweak used; all values are the source idea's. No tuning on valid.
Costs per config/default.yaml (scorer). Educational only - not financial advice."""
SIDE = "long"
GEOM = "S"
WINDOW = (1030, 1430)
SYMBOLS = ["SPY", "QQQ"]
CONTEXT = ["breadth"]
LAYERS = ["SPY/QQQ", "breadth >= 0.70 at 10:30 and >= 0.60 every bar since", "SPY above VWAP every bar since 10:00",
          "pullback: low <= EMA9 or within 0.05% of VWAP, close > VWAP, breadth >= 0.50",
          "first bar after the touch closing > EMA9 and > prior high", "stop VWAP - 0.10 ATR, target HOD + 0.10 ATR",
          "10:30-14:30 ET"]

import sys
from pathlib import Path

import numpy as np
import pandas as pd

_ST = {}
_DC = {}


def _f(df, c):
    return df[c].to_numpy(float) if c in df else np.full(len(df), np.nan)


def _key(df):
    """Symbol-day group code (frames are sorted by symbol, date, tod, so groups are contiguous)."""
    s = pd.Series(df["symbol"].astype(str).to_numpy()) + "|" + pd.Series(df["date"].astype(str).to_numpy())
    return pd.factorize(s)[0]


def _start(k):
    return np.r_[True, k[1:] != k[:-1]] if len(k) else np.zeros(0, bool)


def _lag(x, k, n=1):
    """x from n bars earlier in the same symbol-day (NaN across a day boundary)."""
    x = np.asarray(x, float)
    p = np.full(len(x), np.nan)
    if len(x) > n:
        p[n:] = x[:-n]
        p[n:][k[n:] != k[:-n]] = np.nan
    return p


def _gcum(x, k):
    """Inclusive running sum within each symbol-day."""
    x = np.asarray(x, float)
    cs = np.cumsum(x)
    st = _start(k)
    base = (cs - x)[st]
    return cs - base[np.cumsum(st) - 1]


def _gacc(x, k, fn):
    """Inclusive running max / min (fn = np.fmax / np.fmin) within each symbol-day, ignoring NaN."""
    s = pd.Series(np.asarray(x, float))
    g = s.groupby(k)
    return (g.cummax() if fn is np.fmax else g.cummin()).to_numpy(float)


def _first(cond, k):
    """True only on the first True row of each symbol-day."""
    cond = np.asarray(cond, bool)
    return cond & ((_gcum(cond, k) - cond) == 0)


def _at(x, k, tod, T):
    """Value of x on the bar closing at T, broadcast to its symbol-day. Use only on rows with tod >= T."""
    gv = np.full(int(k.max()) + 1 if len(k) else 1, np.nan)
    sel = tod == T
    gv[k[sel]] = np.asarray(x, float)[sel]
    return gv[k]


def _sym_ctx(df, sym, x):
    """Column x of symbol `sym` at the same (date, tod) as each row (NaN when that symbol's bar is missing)."""
    s = df["symbol"].astype(str).to_numpy()
    sel = s == sym
    if not sel.any():
        return np.full(len(df), np.nan)
    d = df["date"].astype(str).to_numpy()
    t = df["tod"].to_numpy(np.int64)
    ser = pd.Series(np.asarray(x, float)[sel], index=pd.MultiIndex.from_arrays([d[sel], t[sel]]))
    ser = ser[~ser.index.duplicated()]
    return ser.reindex(pd.MultiIndex.from_arrays([d, t])).to_numpy(float)


def _stash_get(f, i, j):
    s = _ST.get(id(f))
    if s is None or len(s[0]) != len(f):
        mask(f)
        s = _ST.get(id(f))
    return float(s[j][i]) if s is not None else float("nan")


def stop_price(f, i):
    return _stash_get(f, i, 0)


def target_price(f, i, stop):
    return _stash_get(f, i, 1)


def mask(df) -> np.ndarray:
    _ST.clear()
    z = np.zeros(len(df), dtype=bool)
    if not len(df) or "breadth" not in df:
        return z
    k = _key(df)
    tod = df["tod"].to_numpy(np.int64)
    c, h, l, atr = _f(df, "close"), _f(df, "high"), _f(df, "low"), _f(df, "atr_d")
    vd = _f(df, "vwapDistPct")
    br = _f(df, "breadth")
    sym = df["symbol"].astype(str)
    ema9 = pd.Series(c).groupby(sym.to_numpy()).transform(lambda x: x.ewm(span=9, adjust=False).mean()).to_numpy(float)
    with np.errstate(invalid="ignore", divide="ignore"):
        vwap = c / (1 + vd / 100)
        hod = c + _f(df, "dist_hod_atr") * atr
        # 1. breadth trend day
        br1030 = _at(br, k, tod, 1030)
        brmin = _gacc(np.where(tod >= 1030, br, np.nan), k, np.fmin)
        g1 = (tod >= 1030) & (br1030 >= 0.70) & (brmin >= 0.60)
        # 2. SPY above VWAP on every bar since 10:00
        spy_vd = _sym_ctx(df, "SPY", vd)
        spy_bad = np.where(tod >= 1000, ~(spy_vd > 0), False).astype(float)
        g2 = (_gcum(spy_bad, k) == 0) & (tod >= 1000)
        # 3. touch bar (at or after 10:30)
        touch = (tod >= 1030) & ((l <= ema9) | (l <= vwap * 1.0005)) & (c > vwap) & (br >= 0.50)
        had_touch = (_gcum(touch.astype(float), k) - touch) > 0      # a touch on an EARLIER bar
        # 4. trigger
        trig = (c > ema9) & (c > _lag(h, k)) & had_touch
        m = g1 & g2 & trig & (c > vwap)
        m &= (tod >= WINDOW[0]) & (tod <= WINDOW[1])
        stop = vwap - 0.10 * atr
        tgt = hod + 0.10 * atr
        m &= (stop < c) & (tgt > c)
    _ST[id(df)] = (stop, tgt)
    return np.asarray(m, dtype=bool)
