"""pod-of-defended-origin-retest-g025-long - Light-volume return to the origin of a high-volume impulse bar (LONG).

Source: Jigsaw Trading (Peter Davies) 'Practical Application of Order Flow' (return to a defended area; healthy
pullbacks have little participation).
URL: https://www.jigsawtrading.com/wp-content/uploads/2014/03/PracticalApplicationOfOrderFlow-Pt1.pdf

VARIANT of R08 bull flag (<= 50% retrace) and BLK Trader Dale block POC retest (origin = a consolidation block).
Stated change: a FULL retrace to a single high-volume impulse bar's low on light volume, bought at the origin.
Rules (plain English):
  1. Impulse bar I (bar close 10:00-13:30): volumeRatio >= 2.5, close-to-close gain >= 0.25 x atr_d,
     pricePosition >= 0.999 (a 20-bar closing high), close > session VWAP.
  2. 6-18 bars after I, this bar's low is within 0.10 x atr_d of I's low (or below it) and no close since I
     (this bar included) is below I's low. The most recent qualifying I is used.
  3. This bar: volumeRatio <= 0.8 and flow3 > -0.3.
  4. This bar closes above I's low with lower_wick >= 0.3.
  5. breadth >= 0.45.
  Entry: close, bar close 10:30-14:30. Stop (GEOM S): I low - 0.15 x atr_d. Target: I high, else flat 15:55.
ONE pre-declared tweak (set before any scoring of this file, not tuned on the valid period): the
impulse size 0.4 -> 0.25 x atr_d. The source only says 'a high-volume impulse bar' and gives no size; the
0.4 base gave about 8 impulse bars a month (June 2025) and 0 trades.
Costs per config/default.yaml (applied by the scorer). Only bars up to the decision bar are used; prior-day
values come from completed days only.
Educational only - not financial advice."""
SIDE = "long"
GEOM = "S"
WINDOW = (1030, 1430)
CONTEXT = ['breadth']
LAYERS = ['impulse bar vr >= 2.5, +GAIN ATR, 20-bar high, above VWAP', '6-18 bars later back to I low, no close below', 'touch vr <= 0.8, flow3 > -0.3', 'touch closes above I low, lower wick >= 0.3', 'breadth >= 0.45', 'stop I low - 0.15 ATR, target I high']

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
    return np.r_[True, k[1:] != k[:-1]]


def _lag(x, k, n=1):
    """x from n bars earlier in the same symbol-day k (NaN when that bar is in another group)."""
    x = np.asarray(x, float)
    p = np.full(len(x), np.nan)
    if len(x) > n:
        p[n:] = x[:-n]
        p[n:][k[n:] != k[:-n]] = np.nan
    return p


def _gcum(x, k):
    """Inclusive running sum within each group k."""
    x = np.asarray(x, float)
    cs = np.cumsum(x)
    st = _start(k)
    base = (cs - x)[st]
    return cs - base[np.cumsum(st) - 1]


def _gcummax(x, k):
    return pd.Series(np.asarray(x, float)).groupby(k).cummax().to_numpy(float)


def _gcummin(x, k):
    return pd.Series(np.asarray(x, float)).groupby(k).cummin().to_numpy(float)


def _runlen(cond, k):
    """Number of consecutive True bars ending at (and including) each bar, within the symbol-day."""
    cond = np.asarray(cond, bool)
    grp = np.cumsum(~cond | _start(k))           # new block whenever cond is False or a new day starts
    cnt = pd.Series(cond.astype(float)).groupby(grp).cumsum().to_numpy(float)
    return np.where(cond, cnt, 0.0)


def _at(x, k, tod, T):
    """Value of x on the bar that closes at T, broadcast to its symbol-day. Used only on rows with tod > T."""
    gv = np.full(int(k.max()) + 1 if len(k) else 1, np.nan)
    sel = tod == T
    gv[k[sel]] = np.asarray(x, float)[sel]
    return gv[k]


def _base(df):
    k = _key(df)
    tod = df["tod"].to_numpy(np.int64)
    c = _f(df, "close")
    atr = _f(df, "atr_d")
    b = dict(k=k, tod=tod, c=c, h=_f(df, "high"), l=_f(df, "low"), atr=atr)
    b["hod"] = c + _f(df, "dist_hod_atr") * atr          # running high of day (includes 09:30-09:45)
    b["lod"] = c - _f(df, "dist_lod_atr") * atr
    b["pdh"] = c + _f(df, "dist_pdh_atr") * atr          # prior completed day's high
    b["pdl"] = c - _f(df, "dist_pdl_atr") * atr
    b["opn"] = c / (1 + _f(df, "fromOpen") / 100)        # today's open
    b["pc"] = b["opn"] / (1 + _f(df, "gap") / 100)        # prior close
    b["vwap"] = c / (1 + _f(df, "vwapDistPct") / 100)
    b["atr5"] = _f(df, "atrPct") * c / 100                # 5-minute ATR(14), $
    return b


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


def target_price(f, i, stop):
    return _stash_get(f, i, 1)

GAIN = 0.25


def mask(df) -> np.ndarray:
    z = np.zeros(len(df), dtype=bool)
    _ST.clear()
    if not len(df) or "breadth" not in df:
        return z
    b = _base(df)
    k, tod, c, h, l, atr = b["k"], b["tod"], b["c"], b["h"], b["l"], b["atr"]
    vr, fl3, pp = _f(df, "volumeRatio"), _f(df, "flow3"), _f(df, "pricePosition")
    with np.errstate(invalid="ignore", divide="ignore"):
        imp = (vr >= 2.5) & ((c - _lag(c, k)) >= GAIN * atr) & (pp >= 0.999) & (c > b["vwap"]) \
            & (tod >= 1000) & (tod <= 1330)                                                   # (1)
        imp = imp.astype(float)
        touch = (vr <= 0.8) & (fl3 > -0.3) & (_f(df, "lower_wick") >= 0.3) & (_f(df, "breadth") >= 0.45)  # (3)(5)
        stop = np.full(len(c), np.nan)
        tgt = np.full(len(c), np.nan)
        m = np.zeros(len(c), bool)
        minc = c.copy()                          # min close over bars I+1 .. now, built as j grows
        for j in range(1, 19):
            if j > 1:
                minc = np.fmin(minc, _lag(c, k, j - 1))
            if j < 6:
                continue
            il = _lag(l, k, j)
            ok = (_lag(imp, k, j) == 1) & (l <= il + 0.10 * atr) & (minc >= il) & (c > il)   # (2)(4)
            ok &= ~m                              # keep the most recent I (smallest j)
            stop = np.where(ok, il - 0.15 * atr, stop)
            tgt = np.where(ok, _lag(h, k, j), tgt)
            m |= ok
        m &= touch & (tgt > c)
        m &= (tod >= WINDOW[0]) & (tod <= WINDOW[1])
    _ST[id(df)] = (stop, tgt)
    return np.asarray(m & np.isfinite(stop) & np.isfinite(tgt), dtype=bool)
