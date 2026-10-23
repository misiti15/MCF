"""pod-raschke-trendday-d2-prior-close-hold-long - Day after a trend-up close: buy the morning test of the prior close
that holds (LONG).

Source: Linda Raschke - 'Street Smarts' (Raschke & Connors 1995, trend-day follow-through) and 'Trading Sardines'
(2019); Raschke interview in Schwager, 'The New Market Wizards'. Not re-fetched in round 2 (search budget used up,
WebFetch DNS failure); the rules are rebuilt from the published method.
URL: https://lbrgroup.com

VARIANT of pod-smb-day2-drive-pullback-long (needs a D-1 change of +5% or more, enters on a VWAP / SMA20 pullback) and
pod-edgeful-green-first15-open-hold-long (tests today's open with no D-1 filter). Stated change: a D-1 trend-day
close-location filter, with the entry at the prior close level.

Rules (plain English, LONG). Derived levels (all from completed D-1 values or bars up to this one):
open = close/(1+fromOpen/100); pc = open/(1+gap/100); PDH = close + dist_pdh_atr x atr_d; PDL = close - dist_pdl_atr x
atr_d; CL = (pc - PDL)/(PDH - PDL); LOD = close - dist_lod_atr x atr_d; HOD = close + dist_hod_atr x atr_d.
  1. CL >= 0.85 and (PDH - PDL) >= 1.0 x atr_d: D-1 closed near its high on a wide day.
  2. gap between -0.3% and +1.5% (not a big day-2 gapper).
  3. Trigger bar: low <= pc + 0.10 x atr_d, close >= pc + 0.05 x atr_d, lower_wick >= 0.4.
  4. LOD >= pc - 0.15 x atr_d (the prior close holds).
  5. spy_fo > -0.3.
  Bar close 10:00-11:45; first trigger per symbol-day (the scorer's no-refire rule).
  Entry: the trigger bar's close. Stop (GEOM S): LOD - 0.05 x atr_d; skip when entry - stop > 0.5 x atr_d. Target:
  the HOD as of the entry bar or entry + 1.5R, whichever is nearer (comes first for a long); when the HOD is not above
  the entry, 1.5R. Else flat 15:55.
No tweak used; all values as stated. No tuning on valid. Costs per config/default.yaml (scorer).
Educational only - not financial advice."""
SIDE = "long"
GEOM = "S"
WINDOW = (1000, 1145)
CONTEXT = ["spy_fo"]
LAYERS = ["D-1 CL >= 0.85 and range >= 1 ATR", "gap -0.3..+1.5%", "low <= pc + 0.10 ATR, close >= pc + 0.05 ATR",
          "lower_wick >= 0.4", "LOD >= pc - 0.15 ATR", "spy_fo > -0.3", "risk <= 0.5 ATR",
          "stop LOD - 0.05 ATR, target min(HOD, 1.5R)", "10:00-11:45 ET"]

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
    if not len(df) or "spy_fo" not in df:
        return z
    tod = df["tod"].to_numpy(np.int64)
    c, l, atr = _f(df, "close"), _f(df, "low"), _f(df, "atr_d")
    fo, gap = _f(df, "fromOpen"), _f(df, "gap")
    with np.errstate(invalid="ignore", divide="ignore"):
        opn = c / (1 + fo / 100)
        pc = opn / (1 + gap / 100)
        pdh = c + _f(df, "dist_pdh_atr") * atr
        pdl = c - _f(df, "dist_pdl_atr") * atr
        cl = (pc - pdl) / (pdh - pdl)
        lod = c - _f(df, "dist_lod_atr") * atr
        hod = c + _f(df, "dist_hod_atr") * atr
        m = (cl >= 0.85) & ((pdh - pdl) >= 1.0 * atr)
        m &= (gap >= -0.3) & (gap <= 1.5)
        m &= (l <= pc + 0.10 * atr) & (c >= pc + 0.05 * atr) & (_f(df, "lower_wick") >= 0.4)
        m &= lod >= pc - 0.15 * atr
        m &= _f(df, "spy_fo") > -0.3
        m &= (tod >= WINDOW[0]) & (tod <= WINDOW[1])
        stop = lod - 0.05 * atr
        risk = c - stop
        m &= (risk > 0) & (risk <= 0.5 * atr)
        t15 = c + 1.5 * risk
        tgt = np.where(hod > c, np.fmin(hod, t15), t15)
    _ST[id(df)] = (stop, tgt)
    return np.asarray(m, dtype=bool)
