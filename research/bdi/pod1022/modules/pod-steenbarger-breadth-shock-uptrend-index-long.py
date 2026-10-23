"""pod-steenbarger-breadth-shock-uptrend-index-long - Buy a sudden breadth washout on an index up-day ('buy TICK lows in
an uptrend') (LONG).

Source: Brett Steenbarger, TraderFeed blog and podcast interviews (buy NYSE TICK extremes against the trend; the
uptrend shows in internals). Written from memory, URL not re-checked.
URL: https://traderfeed.blogspot.com/

VARIANT of pod-breadth-trendday-index-pullback-long. Stated change: the trigger is a breadth SHOCK (breadth falls
>= 0.20 within 15 minutes), which the parent rules out (it requires breadth >= 0.50 on the pullback); entry on the
breadth snap-back, not an EMA9 touch. Also differs from pod-smb-market-flush-holder-long (down market, strong stocks).

Rules (plain English, LONG). SYMBOLS SPY, QQQ, IWM. breadth = share of the universe above its own VWAP (TICK proxy).
Decision bar i, bar close 10:30-14:30; all look-backs are same-day bars.
  1. Up-day: spy_fo >= +0.4% at bar i-4, and SPY closed above its session VWAP on every bar from 10:00 to i-4 (SPY's
     own rows).
  2. Shock: min(breadth over bars i-3..i-1) <= breadth[i-4] - 0.20.
  3. Snap: breadth[i] >= breadth[i-1] + 0.05, and the ETF closes above the previous bar's high.
  4. The ETF close >= its session VWAP - 0.10 x atr_d.
  Entry: close. Stop (GEOM S): min low of bars i-3..i - 0.05 x atr_d. Target: HOD as of entry when it is >= 0.8 x
  risk above the entry, otherwise entry + 1R. Flat 15:55.
No tweak used; all values as stated. No tuning on valid. Costs per config/default.yaml (scorer).
Educational only - not financial advice."""
SIDE = "long"
GEOM = "S"
WINDOW = (1030, 1430)
SYMBOLS = ["SPY", "QQQ", "IWM"]
CONTEXT = ["breadth", "spy_fo"]
LAYERS = ["SPY/QQQ/IWM", "spy_fo >= 0.4 at i-4 and SPY above VWAP 10:00..i-4", "breadth drop >= 0.20 in i-3..i-1",
          "breadth up >= 0.05 on i, close > prior high", "close >= VWAP - 0.10 ATR",
          "stop min low i-3..i - 0.05 ATR, target HOD if >= 0.8R else 1R", "10:30-14:30 ET"]

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
    if not len(df) or "breadth" not in df or "spy_fo" not in df:
        return z
    k = _key(df)
    tod = df["tod"].to_numpy(np.int64)
    c, h, l, atr = _f(df, "close"), _f(df, "high"), _f(df, "low"), _f(df, "atr_d")
    vd = _f(df, "vwapDistPct")
    br = _f(df, "breadth")
    with np.errstate(invalid="ignore", divide="ignore"):
        vwap = c / (1 + vd / 100)
        hod = c + _f(df, "dist_hod_atr") * atr
        spy_vd = _sym_ctx(df, "SPY", vd)
        bad = np.where(tod >= 1000, ~(spy_vd > 0), False).astype(float)
        bad4 = _lag(_gcum(bad, k), k, 4)
        tod4 = _lag(tod.astype(float), k, 4)
        g1 = (_lag(_f(df, "spy_fo"), k, 4) >= 0.4) & (bad4 == 0) & (tod4 >= 1000)
        b1, b2, b3, b4 = (_lag(br, k, n) for n in (1, 2, 3, 4))
        bmin = np.fmin(np.fmin(b1, b2), b3)
        g2 = np.isfinite(b1) & np.isfinite(b2) & np.isfinite(b3) & (bmin <= b4 - 0.20)
        g3 = (br >= b1 + 0.05) & (c > _lag(h, k))
        g4 = c >= vwap - 0.10 * atr
        m = g1 & g2 & g3 & g4 & (tod >= WINDOW[0]) & (tod <= WINDOW[1])
        lmin = np.fmin(np.fmin(np.fmin(_lag(l, k, 1), _lag(l, k, 2)), _lag(l, k, 3)), l)
        stop = lmin - 0.05 * atr
        risk = c - stop
        tgt = np.where(hod >= c + 0.8 * risk, hod, c + risk)
    _ST[id(df)] = (stop, tgt)
    return np.asarray(m, dtype=bool)
