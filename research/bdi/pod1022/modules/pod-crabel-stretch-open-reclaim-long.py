"""pod-crabel-stretch-open-reclaim-long - Crabel stretch failure: after an early drop of at least one stretch below
today's open, buy the reclaim of the open (LONG).

Source: Toby Crabel, 'Day Trading with Short Term Price Patterns and Opening Range Breakout' (1990), the 'stretch'
concept (often discussed on Better System Trader). NOT verified against a specific episode (web blocked this run).
URL: https://bettersystemtrader.com (podcast; no specific episode verified)

VARIANT of Reddit R06-red-green (red-to-green / green-to-red through the PRIOR CLOSE). Stated changes: the pivot is
TODAY'S OPEN, an earlier excursion of at least one stretch below the open is required, and only small-gap days qualify.

Rules (plain English, LONG). Derived: open = close / (1 + fromOpen/100); LOD = close - dist_lod_atr x atr_d (low of day
as of this bar). Stretch fixed at 0.30 x daily ATR (Crabel's stretch is an average open-to-extreme distance; a fixed
ATR fraction is the proxy here).
  1. Bar close 10:00-12:00.
  2. |gap| <= 1.0%.
  3. (open - LOD) / atr_d >= 0.30: the stretch excursion below the open has happened.
  4. fromOpen <= 0 on the previous bar (same symbol-day) and > 0 on this bar: the reclaim of the open.
  5. volumeRatio >= 1.2.
  Entry: that bar's close. Stop (GEOM S): LOD - 0.05 x atr_d. Target: open + (open - LOD), a measured move; else flat
  15:55.
No tweak used; all values as stated. No tuning on valid. Costs per config/default.yaml (scorer).
Educational only - not financial advice."""
SIDE = "long"
GEOM = "S"
WINDOW = (1000, 1200)
CONTEXT = []
LAYERS = ["|gap| <= 1%", "open - LOD >= 0.30 ATR (stretch)", "fromOpen crosses above 0 on this bar",
          "volumeRatio >= 1.2", "stop LOD - 0.05 ATR, target open + (open - LOD)", "10:00-12:00 ET"]

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


def _first(cond, k):
    """True only on the first True row of each symbol-day."""
    cond = np.asarray(cond, bool)
    return cond & ((_gcum(cond, k) - cond) == 0)


def _date_table(df, col):
    """One row per (date, tod) with the market-wide column `col` (same value for every symbol), sorted."""
    t = pd.DataFrame({"date": df["date"].astype(str).to_numpy(), "tod": df["tod"].to_numpy(np.int64),
                      "v": _f(df, col)})
    t = t.dropna(subset=["v"]).drop_duplicates(["date", "tod"]).sort_values(["date", "tod"]).reset_index(drop=True)
    return t


def _map_back(df, t, cols):
    """Map (date, tod) table columns back to the rows of df."""
    idx = pd.MultiIndex.from_arrays([t["date"].to_numpy(), t["tod"].to_numpy()])
    q = pd.MultiIndex.from_arrays([df["date"].astype(str).to_numpy(), df["tod"].to_numpy(np.int64)])
    return {c: pd.Series(t[c].to_numpy(float), index=idx).reindex(q).to_numpy(float) for c in cols}


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
    c, atr, fo = _f(df, "close"), _f(df, "atr_d"), _f(df, "fromOpen")
    with np.errstate(invalid="ignore", divide="ignore"):
        opn = c / (1 + fo / 100)
        lod = c - _f(df, "dist_lod_atr") * atr
        m = np.abs(_f(df, "gap")) <= 1.0
        m &= (opn - lod) / atr >= 0.30
        m &= (_lag(fo, k) <= 0) & (fo > 0)
        m &= _f(df, "volumeRatio") >= 1.2
        m &= (tod >= WINDOW[0]) & (tod <= WINDOW[1])
        stop = lod - 0.05 * atr
        tgt = opn + (opn - lod)
        m &= (stop < c) & (tgt > c)
    _ST[id(df)] = (stop, tgt)
    return np.asarray(m, dtype=bool)
