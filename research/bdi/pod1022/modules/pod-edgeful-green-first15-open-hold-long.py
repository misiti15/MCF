"""pod-edgeful-green-first15-open-hold-long - Green opening (stock and SPY): buy the first pullback that holds today's
open (LONG).

Source: TradeThatSwing (Cory Mitchell, from edgeful data): a green first 15-min SPY candle closes above the open about
70% of the time.
URL: https://tradethatswing.com/high-probability-stock-market-statistics/

VARIANT of R06 / wi-red-to-green (prior close cross, failed) and bdi1013-limit945-dip-entry (failed on spread costs).
Different from pod-dalton-open-drive-pullback (shallow pullback well above the open). Stated change: a green-opening
gate for both stock and SPY, a 10:00-12:00 pullback that holds today's OPEN, market entry after 10:00.

Rules (plain English):
  1. Green opening: fromOpen > 0 on the 09:50 bar for the stock, and spy_fo > 0 on the 09:50 bar (proxy for the
     09:30-09:45 candle colour; the history frames start at the 09:50 bar).
  2. Pullback to the open: the prior bar (the pullback bar) closed within 0.10 x atr_d above today's open (open <=
     close <= open + 0.10 x atr_d) after the stock had been >= 0.35 x atr_d above the open (HOD as of the pullback
     bar); the low of day never below open - 0.05 x atr_d (as of the entry bar).
  3. rsi5 <= 30 on the prior (pullback) bar, and this bar closes above the prior close.
  4. spy_fo > 0 on this bar.
  Entry: that close, bar close 10:00-12:00. Stop (GEOM S): open - 0.15 x atr_d. Target: HOD (as of the entry bar),
  else flat 15:55; no trade when HOD is not above the entry.
Pre-declared reading: the 'close within 0.10 x atr_d' applies to the pullback bar (the rsi5 bar). No tweak used.
No tuning on valid. Costs per config/default.yaml (scorer). Educational only - not financial advice."""
SIDE = "long"
GEOM = "S"
WINDOW = (1000, 1200)
CONTEXT = ["spy_fo"]
LAYERS = ["fromOpen > 0 and spy_fo > 0 at 09:50", "prior close within 0.10 ATR above open after >= 0.35 ATR above",
          "LOD >= open - 0.05 ATR", "rsi5 <= 30 prior bar, close > prior close", "spy_fo > 0",
          "stop open - 0.15 ATR, target HOD", "10:00-12:00 ET"]

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
    if not len(df) or "spy_fo" not in df:
        return z
    k = _key(df)
    tod = df["tod"].to_numpy(np.int64)
    c, atr = _f(df, "close"), _f(df, "atr_d")
    fo, sfo = _f(df, "fromOpen"), _f(df, "spy_fo")
    with np.errstate(invalid="ignore", divide="ignore"):
        opn = c / (1 + fo / 100)
        hod = c + _f(df, "dist_hod_atr") * atr
        lod = c - _f(df, "dist_lod_atr") * atr
        m = (_at(fo, k, tod, 950) > 0) & (_at(sfo, k, tod, 950) > 0)
        pc = _lag(c, k)
        m &= (pc >= opn) & (pc <= opn + 0.10 * atr)
        m &= (_lag(hod, k) - opn) >= 0.35 * atr
        m &= lod >= opn - 0.05 * atr
        m &= (_lag(_f(df, "rsi5"), k) <= 30) & (c > pc)
        m &= sfo > 0
        m &= (tod >= WINDOW[0]) & (tod <= WINDOW[1])
        stop = opn - 0.15 * atr
        tgt = hod
        m &= (tgt > c) & (stop < c)
    _ST[id(df)] = (stop, tgt)
    return np.asarray(m, dtype=bool)
