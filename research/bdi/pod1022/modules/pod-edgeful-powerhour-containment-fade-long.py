"""pod-edgeful-powerhour-containment-fade-long - Pre-power-hour containment: fade a quiet approach to the LOD on a
quiet day (LONG side; the source idea is both sides, scored as two modules).

Source: edgeful 'power hour breakout' report and blog (most days make no new HOD/LOD in the last hour).
URL: https://www.edgeful.com/blog/posts/power-hour-breakout-report

VARIANT of exhaustion_short (Testing: afternoon new-high RSI5 > 90 climax) and CWT14 failed breaks. Stated change: no
break and no climax - the trade is the containment of the day range on quiet days, both sides, light-volume approach.

Rules (plain English), decision bar i (SHORT; the LONG module is the exact mirror at the LOD with rsi5 <= 25):
  1. Quiet day: day range so far (HOD - LOD) <= 1.0 x atr_d and |fromOpen| <= 0.6 x atr_d / close (in %).
  2. Approach: close within 0.10 x atr_d of the HOD; no new HOD in the 3 bars before the approach bar (the HOD as of
     bar i-1 equals the HOD as of bar i-4).
  3. rsi5 >= 75 and volumeRatio <= 1.0 (light-volume approach).
  4. SPY is not making a new HOD on this bar (SPY's own row at the same date/tod: its high of day rose on this bar ->
     no trade; no SPY row -> no trade).
  Entry: close. Stop (GEOM S): HOD + 0.15 x atr_d. Target: session VWAP or the day-range midpoint, whichever is closer
  (and below the entry; if neither is, no trade). Flat 15:55. Bar close 14:00-15:00.
  This module: LONG, rsi5 <= 25, level LOD. No tweak used. Only bars up to the decision bar. Costs in (scorer).
Educational only - not financial advice."""
SIDE = "long"
GEOM = "S"
WINDOW = (1400, 1500)
CONTEXT = []
LAYERS = ["day range <= 1.0 ATR, |fromOpen| <= 0.6 ATR", "close within 0.10 ATR of the LOD, no new LOD in 3 prior bars",
          "rsi5 <= 25, volumeRatio <= 1.0", "SPY not making a new LOD on the bar",
          "stop LOD -/+ 0.15 ATR, target nearer of VWAP / range midpoint", "14:00-15:00 ET"]
import numpy as np
import pandas as pd

_ST = {}


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


def _at(x, k, tod, T):
    """Value of x on the bar closing at T, broadcast to its symbol-day. Use only on rows with tod >= T."""
    gv = np.full(int(k.max()) + 1 if len(k) else 1, np.nan)
    sel = tod == T
    gv[k[sel]] = np.asarray(x, float)[sel]
    return gv[k]


def _stash_get(f, i, j):
    s = _ST.get(id(f))
    if s is None or len(s[0]) != len(f):
        mask(f)
        s = _ST.get(id(f))
    if s is None or s[j] is None:
        return float("nan")
    return float(s[j][i])


def stop_price(f, i):
    return _stash_get(f, i, 0)


def _spy_new_ext(df, k, tod, side):
    """(date, tod) keys where SPY's running HOD (short) / LOD (long) moved on that bar, from SPY's own rows."""
    sym = df["symbol"].astype(str).to_numpy()
    sel = sym == "SPY"
    if not sel.any():
        return None
    c, atr = _f(df, "close"), _f(df, "atr_d")
    if side == "short":
        ext = c + _f(df, "dist_hod_atr") * atr
        new = ext > _lag(ext, k, 1) + 1e-9
    else:
        ext = c - _f(df, "dist_lod_atr") * atr
        new = ext < _lag(ext, k, 1) - 1e-9
    d = df["date"].astype(str).to_numpy()
    spy = pd.Series(new[sel], index=pd.MultiIndex.from_arrays([d[sel], tod[sel].astype(int)]))
    spy = spy[~spy.index.duplicated()]
    keys = pd.MultiIndex.from_arrays([d, tod.astype(int)])
    known = keys.isin(spy.index)
    flag = np.ones(len(df), bool)                       # unknown -> treated as "SPY new extreme" -> no trade
    flag[known] = spy.reindex(keys[known]).to_numpy(bool)
    return flag


def mask(df) -> np.ndarray:
    z = np.zeros(len(df), dtype=bool)
    _ST.clear()
    if not len(df):
        return z
    k = _key(df)
    tod = df["tod"].to_numpy(np.int64)
    c, atr = _f(df, "close"), _f(df, "atr_d")
    spynew = _spy_new_ext(df, k, tod, SIDE)
    if spynew is None:
        return z
    with np.errstate(invalid="ignore", divide="ignore"):
        hod = c + _f(df, "dist_hod_atr") * atr
        lod = c - _f(df, "dist_lod_atr") * atr
        vwap = c / (1 + _f(df, "vwapDistPct") / 100)
        mid = (hod + lod) / 2
        m = ((hod - lod) <= 1.0 * atr) & (np.abs(_f(df, "fromOpen")) <= 0.6 * atr / c * 100)
        m &= _f(df, "volumeRatio") <= 1.0
        m &= ~spynew
        if SIDE == "short":
            m &= _f(df, "dist_hod_atr") <= 0.10
            m &= _lag(hod, k, 1) <= _lag(hod, k, 4) + 1e-9
            m &= _f(df, "rsi5") >= 75
            stop = hod + 0.15 * atr
            cv = np.where(vwap < c, vwap, -np.inf)
            cm = np.where(mid < c, mid, -np.inf)
            tgt = np.maximum(cv, cm)
            m &= np.isfinite(tgt)
        else:
            m &= _f(df, "dist_lod_atr") <= 0.10
            m &= _lag(lod, k, 1) >= _lag(lod, k, 4) - 1e-9
            m &= _f(df, "rsi5") <= 25
            stop = lod - 0.15 * atr
            cv = np.where(vwap > c, vwap, np.inf)
            cm = np.where(mid > c, mid, np.inf)
            tgt = np.minimum(cv, cm)
            m &= np.isfinite(tgt)
        m &= (tod >= WINDOW[0]) & (tod <= WINDOW[1])
    _ST[id(df)] = (stop, tgt)
    return np.asarray(m, dtype=bool)


def target_price(f, i, stop):
    return _stash_get(f, i, 1)
