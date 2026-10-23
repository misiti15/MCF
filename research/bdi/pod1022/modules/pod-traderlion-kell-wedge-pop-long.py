"""pod-traderlion-kell-wedge-pop-long - Oliver Kell 'wedge pop', intraday: a compression under falling EMAs pops through
EMA9/21 on volume (LONG).

Source: TraderLion podcast / Oliver Kell, 'Cycle of Price Action' (wedge pop, EMA crossback). A new setup from a
channel already mined (existing TraderLion ids: orh60, undercut-rally, insideday-pdh, dryup-ema21-pullback).
Written from memory, URL not re-checked.
URL: https://traderlion.com/podcast/

VARIANT of Reddit R10 EMA 9/21 cross (failed) and t3 rvol consolidation breakout. Stated change: the cross must come
out of a compression that formed BELOW falling EMAs, inside a higher-timeframe uptrend, and must also clear the box
high.

Rules (plain English, LONG). adv20 >= $50M. EMA9 / EMA21 = 5-minute EMAs of close run continuously per symbol.
  1. Higher-TF uptrend: sma50_dist_pct > 0 on the bar 12 bars ago, and today's gap between -1% and +2%.
  2. Pullback and wedge: emaDiff < 0 on at least 8 of the previous 12 bars, and the box height (max high - min low
     over the previous 12 bars) <= 0.35 x atr_d.
  3. Pop bar: close above EMA9 and EMA21, emaDiff >= 0 now and < 0 on the previous bar, close above the 12-bar box
     high, volumeRatio >= 1.8.
  4. spy_fo >= -0.3%.
  Window: bar close 10:30-14:30. Entry is that close. Stop (GEOM S): box low - 0.05 x atr_d, capped at 0.5 x atr_d
  from entry. Target: 2R, otherwise flat 15:55.
Deviation (pre-declared, not tuned): the 12-bar look-back must lie inside today's session (frames start at the 09:50
bar), so the first possible pop bar is 10:50, not 10:30; boxes never straddle the overnight gap.
No tweak used; all values as stated. No tuning on valid. Costs per config/default.yaml (scorer).
Educational only - not financial advice."""
SIDE = "long"
GEOM = "S"
WINDOW = (1030, 1430)
MIN_ADV = 50e6
CONTEXT = ["spy_fo"]
LAYERS = ["adv20 >= 50M", "sma50_dist_pct > 0 twelve bars ago, gap -1..+2%", "emaDiff < 0 on >= 8 of 12 prior bars",
          "12-bar box <= 0.35 ATR", "EMA cross up + close > EMA9/EMA21 + close > box high", "volumeRatio >= 1.8",
          "spy_fo >= -0.3", "stop box low - 0.05 ATR (cap 0.5 ATR), target 2R", "10:30-14:30 ET"]

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
    ed = _f(df, "emaDiff")
    sym = df["symbol"].astype(str).to_numpy()
    cs = pd.Series(c)
    ema9 = cs.groupby(sym).transform(lambda x: x.ewm(span=9, adjust=False).mean()).to_numpy(float)
    ema21 = cs.groupby(sym).transform(lambda x: x.ewm(span=21, adjust=False).mean()).to_numpy(float)
    N = 12
    bh = np.full(len(df), -np.inf)
    bl = np.full(len(df), np.inf)
    neg = np.zeros(len(df))
    full = np.ones(len(df), bool)
    for n in range(1, N + 1):
        hn, ln, en = _lag(h, k, n), _lag(l, k, n), _lag(ed, k, n)
        full &= np.isfinite(hn) & np.isfinite(ln) & np.isfinite(en)
        bh = np.fmax(bh, hn)
        bl = np.fmin(bl, ln)
        with np.errstate(invalid="ignore"):
            neg += (en < 0)
    with np.errstate(invalid="ignore", divide="ignore"):
        gap = _f(df, "gap")
        m = full & (_lag(_f(df, "sma50_dist_pct"), k, N) > 0) & (gap >= -1) & (gap <= 2)
        m &= (neg >= 8) & ((bh - bl) <= 0.35 * atr)
        m &= (c > ema9) & (c > ema21) & (ed >= 0) & (_lag(ed, k) < 0) & (c > bh)
        m &= _f(df, "volumeRatio") >= 1.8
        m &= _f(df, "spy_fo") >= -0.3
        m &= (tod >= WINDOW[0]) & (tod <= WINDOW[1])
        stop = np.fmax(bl - 0.05 * atr, c - 0.5 * atr)
        tgt = c + 2 * (c - stop)
    _ST[id(df)] = (stop, tgt)
    return np.asarray(m, dtype=bool)
