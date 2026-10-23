"""pod-tosind-lunch-compression-index-break-short - Lunch compression on index ETFs: follow the first afternoon break of
the 11:30-12:30 box (SHORT).

Source: tosindicators research 'Can't Trade The Market Open Or Close? Try This Hour Instead' and 'Should You Trade
During The Lunch Time Hour?'.
URL: https://tosindicators.com/research/lunch-trading

VARIANT of wi-ib-narrow-extension (idea) and pod-chop-pop-volume-breakout-long (stocks, long, near HOD). Opposite
logic of pod-of-quiet-midday-range-fail (fades the poke). Stated change: index ETFs only, the box is the fixed
11:30-12:30 hour measured as a ratio to the morning range, side from VWAP, both directions.
Files: -long (upside break) and -short (downside break).

Rules (plain English), SYMBOLS SPY, QQQ, IWM, DIA:
  1. Morning range = HOD - LOD as of the 11:30 bar (09:30-11:30, incl. 09:30-09:45 via dist_hod/lod_atr).
     Box = high / low of the bars closing 11:35..12:30. Box height <= 0.30 x the morning range.
  2. From 12:35 to 15:00: the bar closes outside the box by >= 0.03 x atr_d, with volumeRatio >= 1.3.
  3. Long only if close > session VWAP (above the box); short only if close < VWAP (below the box).
  4. First break only: the first bar of the day closing outside the box by >= 0.03 x atr_d (either side); if that
     bar fails rule 2's volume or rule 3, no trade that day.
  Entry: that close. Stop (GEOM S): box midpoint. Target: box edge +/- 1.5 x box height, else flat 15:55.
No tweak used; all values are the source idea's. No tuning on valid. Costs per config/default.yaml (scorer).
Educational only - not financial advice."""
SIDE = "short"
GEOM = "S"
WINDOW = (1235, 1500)
SYMBOLS = ["SPY", "QQQ", "IWM", "DIA"]
CONTEXT = []
LAYERS = ["SPY/QQQ/IWM/DIA", "11:30-12:30 box height <= 0.30 x 09:30-11:30 range",
          "first close outside the box by >= 0.03 ATR, 12:35-15:00", "volumeRatio >= 1.3", "VWAP side agrees",
          "stop box mid, target edge + 1.5 x box height"]

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
    if not len(df):
        return z
    k = _key(df)
    tod = df["tod"].to_numpy(np.int64)
    c, h, l, atr = _f(df, "close"), _f(df, "high"), _f(df, "low"), _f(df, "atr_d")
    with np.errstate(invalid="ignore", divide="ignore"):
        vwap = c / (1 + _f(df, "vwapDistPct") / 100)
        hod = c + _f(df, "dist_hod_atr") * atr
        lod = c - _f(df, "dist_lod_atr") * atr
        mrng = _at(hod - lod, k, tod, 1130)
        inbox = (tod >= 1135) & (tod <= 1230)
        bhi = _at(_gacc(np.where(inbox, h, np.nan), k, np.fmax), k, tod, 1230)
        blo = _at(_gacc(np.where(inbox, l, np.nan), k, np.fmin), k, tod, 1230)
        bh = bhi - blo
        nbox = _at(_gcum(inbox.astype(float), k), k, tod, 1230)
        ok = (nbox >= 10) & (bh > 0) & (bh <= 0.30 * mrng) & (tod >= 1235) & (tod <= 1500)
        up = ok & (c >= bhi + 0.03 * atr)
        dn = ok & (c <= blo - 0.03 * atr)
        brk = _first(up | dn, k)
        vr = _f(df, "volumeRatio") >= 1.3
        mid = (bhi + blo) / 2
        if SIDE == "long":
            m = brk & up & vr & (c > vwap)
            tgt = bhi + 1.5 * bh
        else:
            m = brk & dn & vr & (c < vwap)
            tgt = blo - 1.5 * bh
        stop = mid
    _ST[id(df)] = (stop, tgt)
    return np.asarray(m, dtype=bool)
