"""pod-hougaard-school-run-2nd15-break-long - Hougaard 'School Run': break of the second 15-minute (09:45-10:00) range.
THIS FILE: LONG side (the idea is two-sided; scored as two files).

Source: Tom Hougaard, 'Best Loser Wins' and his podcast interviews (School Run / Advanced School Run on index
futures). Written from memory: web search budget was used up and WebFetch could not resolve hosts this round, so
the URL is not re-checked.
URL: https://www.tomhougaard.com/

VARIANT of orb20_a and the range-filtered ORB (09:30-09:50 range). Stated change: the range leaves out the first 15
minutes completely and uses only the 09:45-10:00 bars (tod 950, 955, 1000, all in the frame); the trigger window ends
at 11:00; the universe is index-first.

Rules (plain English). Universe: SPY, QQQ, IWM, DIA plus stocks with adv20 >= $500M (MIN_ADV = 500e6; the four
ETFs all clear it).
  1. Range R = max high / min low of the bars closing 09:50, 09:55 and 10:00 (all three must exist). Height between
     0.15 and 0.60 x atr_d.
  2. Long: the first bar close in 10:05-11:00 above R.high (previous close <= R.high), vwapDistPct > 0, spy_fo > 0.
  3. Short mirror: close below R.low (previous close >= R.low), vwapDistPct < 0, spy_fo < 0, SPY gap <= -0.3%.
  4. One trade per symbol-day: only the FIRST bar in 10:05-11:00 that closes outside R on either side may trigger
     (if the day breaks the other side first, it is skipped). Rule 4 of the source ('skip if price already closed
     outside R before 10:05') is automatic here: the frames start at 09:50, and the R bars close inside R.
  Entry: the trigger close. Stop (GEOM S): the opposite side of R, capped at 0.5 x atr_d from entry. Target: entry
  +/- 2 x R height, otherwise flat 15:55.
No tweak used; all values as stated. No tuning on valid. Costs per config/default.yaml (scorer).
Educational only - not financial advice."""
SIDE = "long"
GEOM = "S"
WINDOW = (1005, 1100)
MIN_ADV = 500e6
CONTEXT = ["spy_fo"]
SG = 1
LAYERS = ["adv20 >= 500M (index ETFs first)", "range of the 09:45-10:00 bars, height 0.15-0.60 ATR",
          "first close outside the range in 10:05-11:00", "vwapDistPct sign", "spy_fo sign", "short: SPY gap <= -0.3%",
          "stop opposite side capped 0.5 ATR, target 2 x range", "10:05-11:00 ET"]

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
    c, h, l, atr = _f(df, "close"), _f(df, "high"), _f(df, "low"), _f(df, "atr_d")
    inr = (tod >= 950) & (tod <= 1000)
    kk = pd.Series(k)
    rh = pd.Series(np.where(inr, h, np.nan)).groupby(kk).transform("max").to_numpy(float)
    rl = pd.Series(np.where(inr, l, np.nan)).groupby(kk).transform("min").to_numpy(float)
    nr = pd.Series(inr.astype(float)).groupby(kk).transform("sum").to_numpy(float)
    with np.errstate(invalid="ignore", divide="ignore"):
        ht = rh - rl
        ok = (nr == 3) & (ht >= 0.15 * atr) & (ht <= 0.60 * atr)
        inwin = (tod >= 1005) & (tod <= 1100)
        out = inwin & ((c > rh) | (c < rl))
        first_out = _first(out, k)
        pcl = _lag(c, k)
        vd = _f(df, "vwapDistPct")
        sfo = _f(df, "spy_fo")
        if SG > 0:
            m = first_out & (c > rh) & (pcl <= rh) & (vd > 0) & (sfo > 0)
            stop = np.fmax(rl, c - 0.5 * atr)
        else:
            spy_gap = _sym_ctx(df, "SPY", _f(df, "gap"))
            m = first_out & (c < rl) & (pcl >= rl) & (vd < 0) & (sfo < 0) & (spy_gap <= -0.3)
            stop = np.fmin(rh, c + 0.5 * atr)
        m &= ok
        tgt = c + SG * 2 * ht
        m &= (tod >= WINDOW[0]) & (tod <= WINDOW[1])
    _ST[id(df)] = (stop, tgt)
    return np.asarray(m, dtype=bool)
