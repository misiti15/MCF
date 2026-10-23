"""pod-of-liquidity-vacuum-fill-short - Liquidity-vacuum bar fade: a wide, thin 5-min bar gets half filled (SHORT).

Source: Jigsaw Trading 'Practical Application of Order Flow' (liquidity vacuums); single prints / low-volume nodes
as retest targets (auction market theory).
URL: https://www.jigsawtrading.com/wp-content/uploads/2014/03/PracticalApplicationOfOrderFlow-Pt1.pdf

VARIANT of wi-overreaction-fade and the opposite of the LVN air-pocket continuation (bdi-vid-volume-profile, failed).
Stated change: a single bar that expanded on LOW volume (vacuum, not climax), faded with a half-bar target.
Rules (plain English, SHORT; LONG mirrors):
  1. Bar V (the previous bar): range >= 1.8 x 5-min ATR (atrPct x close of the bar before V), close in the top 25%
     of its range, volumeRatio <= 1.0.
  2. |spy_fo| < 0.5% (quiet tape).
  3. This bar: high <= V high and close < V close (no follow-through).
  Entry: this close, bar close 10:30-14:30. Stop (GEOM S): V high + 0.10 x atr_d. Target: V's 50% level. Flat 15:55.
Pre-declared variant from the source idea: volumeRatio <= 1.0 (base) and <= 0.8 (separate try, file suffix -vr08).
Costs per config/default.yaml (applied by the scorer). Only bars up to the decision bar are used; prior-day
values come from completed days only.
Educational only - not financial advice."""
SIDE = "short"
GEOM = "S"
WINDOW = (1030, 1430)
CONTEXT = ['spy_fo']
LAYERS = ['V: range >= 1.8 x 5m ATR, closes in the far 25%', 'V volumeRatio <= 1.0', '|spy_fo| < 0.5%', 'next bar no new extreme, closes back', 'stop V extreme + 0.10 ATR, target V 50%']

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

VR_MAX = 1.0


def mask(df) -> np.ndarray:
    z = np.zeros(len(df), dtype=bool)
    _ST.clear()
    if not len(df) or "spy_fo" not in df:
        return z
    b = _base(df)
    k, tod, c, h, l, atr, atr5 = b["k"], b["tod"], b["c"], b["h"], b["l"], b["atr"], b["atr5"]
    vr = _f(df, "volumeRatio")
    with np.errstate(invalid="ignore", divide="ignore"):
        hv, lv, cv, vrv = _lag(h, k), _lag(l, k), _lag(c, k), _lag(vr, k)
        rv = hv - lv
        a5 = _lag(atr5, k, 2)                                        # 5m ATR before V
        m = (rv >= 1.8 * a5) & (vrv <= VR_MAX)                         # (1)
        m &= np.abs(_f(df, "spy_fo")) < 0.5                            # (2)
        mid = (hv + lv) / 2
        if SIDE == "short":
            m &= (cv - lv) >= 0.75 * rv
            m &= (h <= hv) & (c < cv)                                  # (3)
            stop = hv + 0.10 * atr
            m &= c > mid
        else:
            m &= (hv - cv) >= 0.75 * rv
            m &= (l >= lv) & (c > cv)
            stop = lv - 0.10 * atr
            m &= c < mid
        tgt = mid
        m &= (tod >= WINDOW[0]) & (tod <= WINDOW[1])
    _ST[id(df)] = (stop, tgt)
    return np.asarray(m & np.isfinite(stop) & np.isfinite(tgt), dtype=bool)
