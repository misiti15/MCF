"""pod-of-absorption-bar-level-long - Absorption bar at LOD/PDL (HOD/PDH): high volume, narrow range, then a break of that bar (LONG).

Source: Jigsaw Trading (Peter Davies) 'Confirming Day Trading Levels with Order Flow' / 'Practical Application of
Order Flow'.
URL: https://www.jigsawtrading.com/wp-content/uploads/2013/11/ConfirmingLevelsWithOrderFlow.pdf

VARIANT of ST8-volspikedn-long (volume spike on a WIDE down bar), CWT05 flush V and the orderflow absorb60 1-second
confirmations. Stated change: effort WITHOUT result on 5-min bars (high volume, NARROW range) at a key level after
aggressive selling, entered only on a confirming break of the absorption bar's high.
Rules (plain English, LONG; SHORT mirrors at HOD / PDH):
  1. Bar A: volumeRatio >= 2.0 and range <= 0.6 x 5-min ATR (atrPct x close).
  2. A's low within 0.15 x atr_d of the low of day (as of A) or of the prior-day low.
  3. flow3 <= -0.3 on the bar before A, and fromOpen at A <= -0.5 x atr_d / close (selling into the level).
  4. A closes in its upper half and lower_wick >= 0.3.
  5. Within the next 2 bars, the first close above A's high = the entry bar (bar A+1 or A+2).
  Entry: that close, bar close 10:00-14:30. Stop (GEOM S): A low - 0.05 x atr_d. Target: 1.5 x the stop distance,
  or session VWAP if it lies between the entry and that target. Flat 15:55.
No tweak made.
Costs per config/default.yaml (applied by the scorer). Only bars up to the decision bar are used; prior-day
values come from completed days only.
Educational only - not financial advice."""
SIDE = "long"
GEOM = "S"
WINDOW = (1000, 1430)
CONTEXT = []
LAYERS = ['A: volumeRatio >= 2, range <= 0.6 x 5m ATR', 'A at LOD/PDL (HOD/PDH) within 0.15 ATR', 'flow3 before A against, fromOpen beyond 0.5 ATR', 'A closes in the favourable half, wick >= 0.3', 'first close beyond A within 2 bars', 'stop A extreme + 0.05 ATR, target 1.5R or VWAP']

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


def mask(df) -> np.ndarray:
    z = np.zeros(len(df), dtype=bool)
    _ST.clear()
    if not len(df):
        return z
    b = _base(df)
    k, tod, c, h, l, atr, atr5 = b["k"], b["tod"], b["c"], b["h"], b["l"], b["atr"], b["atr5"]
    vr, fl3, fo = _f(df, "volumeRatio"), _f(df, "flow3"), _f(df, "fromOpen")
    lw, uw = _f(df, "lower_wick"), _f(df, "upper_wick")
    rng = h - l
    long = SIDE == "long"
    with np.errstate(invalid="ignore", divide="ignore"):
        a = (vr >= 2.0) & (rng <= 0.6 * atr5) & (rng > 0)                                   # (1)
        thr = 0.5 * atr / c * 100
        if long:
            a &= (np.abs(l - b["lod"]) <= 0.15 * atr) | (np.abs(l - b["pdl"]) <= 0.15 * atr)  # (2)
            a &= (_lag(fl3, k) <= -0.3) & (fo <= -thr)                                        # (3)
            a &= ((c - l) >= 0.5 * rng) & (lw >= 0.3)                                         # (4)
            ext = h
        else:
            a &= (np.abs(h - b["hod"]) <= 0.15 * atr) | (np.abs(h - b["pdh"]) <= 0.15 * atr)
            a &= (_lag(fl3, k) >= 0.3) & (fo >= thr)
            a &= ((h - c) >= 0.5 * rng) & (uw >= 0.3)
            ext = l
        a = a.astype(float)
        stop = np.full(len(c), np.nan)
        m = np.zeros(len(c), bool)
        for j in (2, 1):                         # j = 1 (nearest A) wins when both qualify
            aj = _lag(a, k, j) == 1
            ej = _lag(ext, k, j)
            if long:
                trig = c > ej
                if j == 2:
                    trig &= _lag(c, k, 1) <= ej       # first close above A's high
                sj = _lag(l, k, j) - 0.05 * atr
            else:
                trig = c < ej
                if j == 2:
                    trig &= _lag(c, k, 1) >= ej
                sj = _lag(h, k, j) + 0.05 * atr
            ok = aj & trig
            stop = np.where(ok, sj, stop)
            m |= ok
        d = np.abs(c - stop)
        if long:
            tgt = c + 1.5 * d
            vw = b["vwap"]
            tgt = np.where((vw > c) & (vw < tgt), vw, tgt)
            m &= stop < c
        else:
            tgt = c - 1.5 * d
            vw = b["vwap"]
            tgt = np.where((vw < c) & (vw > tgt), vw, tgt)
            m &= stop > c
        m &= (tod >= WINDOW[0]) & (tod <= WINDOW[1])
    _ST[id(df)] = (stop, tgt)
    return np.asarray(m & np.isfinite(stop) & np.isfinite(tgt), dtype=bool)
