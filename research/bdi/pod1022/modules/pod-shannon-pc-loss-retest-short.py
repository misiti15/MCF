"""pod-shannon-pc-loss-retest-short - Gap-up fully filled: short the failed retest of the prior close from below (SHORT).

Source: Brian Shannon / Alpha Trends (the prior close and the gap anchor as reference levels; a failed reclaim marks
the move from stage 3 to stage 4 on the intraday timeframe). Not re-fetched this round (search budget used up,
WebFetch DNS failure).
URL: https://alphatrends.net

VARIANT of CWT02 'First Red Day Short' (needs 3+ up days, shorts the first break below the prior close) and
pod-bst018-andrews-gapzone-fade-F-short (fades from above toward the prior close). Stated change: no multi-day-run
condition; entry only on a failed retest of the prior close from BELOW after the gap has filled.

Rules (plain English, SHORT). pc (prior close) = close / ((1 + fromOpen/100) x (1 + gap/100)).
  1. gap >= +0.5%.
  2. Gap filled: at least one EARLIER bar closing at or after 10:30 closed below pc.
  3. Trigger bar: high >= pc - 0.05 x atr_d (it retests the prior close), close < pc - 0.03 x atr_d (fails), and
     upper_wick >= 0.4.
  4. vwapDistPct < 0 (VWAP overhead).
  5. breadth <= 0.55.
  Entry: close of the trigger bar, bar close 10:45-14:30. Stop (GEOM S): trigger high + 0.05 x atr_d; skip when the
  risk is > 0.5 x atr_d. Target: "LOD or 1.5R" read as whichever comes first, i.e. the NEARER of the low of day so far
  and entry - 1.5R (it must still be below the entry). Flat 15:55.
No tweak used; all values as stated. No tuning on valid. Costs per config/default.yaml (scorer).
Educational only - not financial advice."""
SIDE = "short"
GEOM = "S"
WINDOW = (1045, 1430)
CONTEXT = ["breadth"]
LAYERS = ["gap >= +0.5%", "earlier close < prior close at/after 10:30", "trigger high >= pc - 0.05 ATR, close < pc - 0.03 ATR",
          "upper_wick >= 0.4", "vwapDistPct < 0", "breadth <= 0.55", "stop high + 0.05 ATR (risk <= 0.5 ATR)",
          "target nearer of LOD / 1.5R", "10:45-14:30 ET"]

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
    if not len(df) or "breadth" not in df:
        return z
    k = _key(df)
    tod = df["tod"].to_numpy(np.int64)
    c, h, atr = _f(df, "close"), _f(df, "high"), _f(df, "atr_d")
    gap, fo = _f(df, "gap"), _f(df, "fromOpen")
    with np.errstate(invalid="ignore", divide="ignore"):
        pc = c / ((1 + fo / 100) * (1 + gap / 100))
        lod = c - _f(df, "dist_lod_atr") * atr
        below = ((tod >= 1030) & (c < pc)).astype(float)
        filled_before = (_gcum(below, k) - below) > 0
        m = (gap >= 0.5) & filled_before
        m &= (h >= pc - 0.05 * atr) & (c < pc - 0.03 * atr) & (_f(df, "upper_wick") >= 0.4)
        m &= _f(df, "vwapDistPct") < 0
        m &= _f(df, "breadth") <= 0.55
        m &= (tod >= WINDOW[0]) & (tod <= WINDOW[1])
        stop = h + 0.05 * atr
        risk = stop - c
        m &= (risk > 0) & (risk <= 0.5 * atr)
        tgt = np.fmax(lod, c - 1.5 * risk)
        m &= tgt < c
    _ST[id(df)] = (stop, tgt)
    return np.asarray(m, dtype=bool)
