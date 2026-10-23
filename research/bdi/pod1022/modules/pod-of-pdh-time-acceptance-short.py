"""pod-of-pdh-time-acceptance-short - Time acceptance beyond PDH/PDL (12 closes = two 30-min periods), buy the first pullback (SHORT).

Source: Market Profile acceptance / value-migration rule (Team LBR 'MP Value Area Rule'; Axia Volume Profile course
notes).
URL: http://teamlbr.blogspot.com/2008/09/mp-value-area-rule-80-rule.html

VARIANT of R17 PDH retest (failed) and bdi-reddit-pdhl-break-retest (idea). Stated change: a TIME acceptance
requirement (12 consecutive 5-min closes beyond the level) before a retest counts, and a later window.
Rules (plain English, LONG; SHORT mirrors below PDL):
  1. gap <= +0.3 x atr_d (in % of the prior close) and the open is at or below PDH (open inside the prior range).
  2. Acceptance: the 12 bars before this one all closed above PDH with every low >= PDH - 0.10 x atr_d.
  3. This bar pulls back: -0.15 <= dist_pdh_atr <= 0 (close 0-0.15 ATR above PDH).
  4. This bar: lower_wick >= 0.35 and close above PDH.
  5. breadth >= 0.5 and close > session VWAP.
  Entry: close, bar close 11:00-14:45. Stop (GEOM S): PDH - 0.25 x atr_d. Target: PDH + the prior-day range
  (PDH - PDL); else flat 15:55. (The source offers holdtr or this target; the target was chosen before scoring.)
No tweak made.
Costs per config/default.yaml (applied by the scorer). Only bars up to the decision bar are used; prior-day
values come from completed days only.
Educational only - not financial advice."""
SIDE = "short"
GEOM = "S"
WINDOW = (1100, 1445)
CONTEXT = ['breadth']
LAYERS = ['gap <= 0.3 ATR, open inside the prior range', '12 closes beyond PDH/PDL, lows within 0.10 ATR', 'pullback close 0-0.15 ATR beyond the level', 'wick >= 0.35', 'breadth with the side, VWAP side', 'stop level -/+ 0.25 ATR, target level + prior-day range']

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
    if not len(df) or "breadth" not in df:
        return z
    b = _base(df)
    k, tod, c, h, l, atr = b["k"], b["tod"], b["c"], b["h"], b["l"], b["atr"]
    pdh, pdl = b["pdh"], b["pdl"]
    gap = _f(df, "gap")
    g = 0.3 * atr / b["pc"] * 100
    br = _f(df, "breadth")
    with np.errstate(invalid="ignore", divide="ignore"):
        if SIDE == "long":
            m = (gap <= g) & (b["opn"] <= pdh)                                           # (1)
            run = _runlen((c > pdh) & (l >= pdh - 0.10 * atr), k)
            dd = _f(df, "dist_pdh_atr")
            m &= _lag(run, k) >= 12                                                      # (2)
            m &= (dd >= -0.15) & (dd <= 0) & (c > pdh)                                   # (3)
            m &= _f(df, "lower_wick") >= 0.35                                            # (4)
            m &= (br >= 0.5) & (c > b["vwap"])                                           # (5)
            stop = pdh - 0.25 * atr
            tgt = pdh + (pdh - pdl)
            m &= tgt > c
        else:
            m = (gap >= -g) & (b["opn"] >= pdl)
            run = _runlen((c < pdl) & (h <= pdl + 0.10 * atr), k)
            dd = _f(df, "dist_pdl_atr")
            m &= _lag(run, k) >= 12
            m &= (dd >= -0.15) & (dd <= 0) & (c < pdl)
            m &= _f(df, "upper_wick") >= 0.35
            m &= (br <= 0.5) & (c < b["vwap"])
            stop = pdl + 0.25 * atr
            tgt = pdl - (pdh - pdl)
            m &= tgt < c
        m &= (tod >= WINDOW[0]) & (tod <= WINDOW[1])
    _ST[id(df)] = (stop, tgt)
    return np.asarray(m & np.isfinite(stop) & np.isfinite(tgt), dtype=bool)
