"""pod-of-trapped-breakout-stall-short - High-volume breakout that stalls: short the break of the breakout bar's low (SHORT).

Source: Jigsaw Trading blog 'Trade Video - Using Order Flow to Manage Trades'; Bookmap 'Key Order Flow Strategies:
Breakouts, Trends, Trapped Traders, and Stop Runs'.
URL: https://www.jigsawtrading.com/blog/trade-video-using-order-flow-manage-trades-thin-markets/

VARIANT of CWT14-failbrk-pdh (poke above PDH, close back below); different from pod-wt-stale-base-breakout-fail-short
(weak-volume break of a base). Stated change: an aggressive HIGH-volume close above the level, a 2-4 bar stall, and
the trigger is a close below the breakout bar's LOW; the level may also be the prior 12-bar high.
Rules (plain English):
  1. Bar B closes above the prior-day high (previous close at or below it) or above the high of the 12 bars before
     B, with volumeRatio >= 2.0 and flow3 >= 0.4.
  2. The next 2-4 bars (the stall) make no high above B high + 0.05 x atr_d and do not close below B low.
  3. The bar after the stall (3-5 bars after B) closes below B low; its high is also <= B high + 0.05 x atr_d.
  4. spy_fo <= +0.3%.
  Entry: that close, bar close 10:00-14:30. Stop (GEOM S): the highest high since B (B included) + 0.05 x atr_d.
  Target: 1R, or session VWAP if it lies between the entry and 1R. Flat 15:55.
No tweak made.
Costs per config/default.yaml (applied by the scorer). Only bars up to the decision bar are used; prior-day
values come from completed days only.
Educational only - not financial advice."""
SIDE = "short"
GEOM = "S"
WINDOW = (1000, 1430)
CONTEXT = ['spy_fo']
LAYERS = ['B: close above PDH / 12-bar high, vr >= 2, flow3 >= 0.4', '2-4 bar stall under B high + 0.05 ATR', 'close below B low', 'spy_fo <= +0.3%', 'stop max high + 0.05 ATR, target 1R or VWAP']

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
    if not len(df) or "spy_fo" not in df:
        return z
    b = _base(df)
    k, tod, c, h, l, atr = b["k"], b["tod"], b["c"], b["h"], b["l"], b["atr"]
    vr, fl3 = _f(df, "volumeRatio"), _f(df, "flow3")
    with np.errstate(invalid="ignore", divide="ignore"):
        h12 = np.vstack([_lag(h, k, j) for j in range(1, 13)]).max(axis=0)      # NaN until 12 bars exist
        brk = ((c > b["pdh"]) & (_lag(c, k) <= b["pdh"])) | (c > h12)
        bb = (brk & (vr >= 2.0) & (fl3 >= 0.4)).astype(float)                      # (1)
        stop = np.full(len(c), np.nan)
        m = np.zeros(len(c), bool)
        for j in (3, 4, 5):
            hb, lb = _lag(h, k, j), _lag(l, k, j)
            lim = hb + 0.05 * atr
            ok = (_lag(bb, k, j) == 1) & (c < lb) & (h <= lim)                     # (3)
            mx = hb.copy()
            for s in range(1, j):                                                  # (2) stall bars B+1 .. now-1
                ok &= (_lag(h, k, s) <= lim) & (_lag(c, k, s) >= lb)
                mx = np.fmax(mx, _lag(h, k, s))
            mx = np.fmax(mx, h)
            ok &= ~m
            stop = np.where(ok, mx + 0.05 * atr, stop)
            m |= ok
        m &= _f(df, "spy_fo") <= 0.3                                               # (4)
        d = stop - c
        tgt = c - d
        vw = b["vwap"]
        tgt = np.where((vw < c) & (vw > tgt), vw, tgt)
        m &= d > 0
        m &= (tod >= WINDOW[0]) & (tod <= WINDOW[1])
    _ST[id(df)] = (stop, tgt)
    return np.asarray(m & np.isfinite(stop) & np.isfinite(tgt), dtype=bool)
