"""pod-brooks-wedge-bottom-long - Three-push wedge bottom on a non-trend day (LONG).

Source: Al Brooks, 'Trading Price Action Trading Ranges' / Brooks Trading Course (wedge bottom = three pushes down).
The URL was not re-checked this round.
URL: https://www.brookstradingcourse.com/

VARIANT of pod-brooks-range-day-edge-fade (position in the day range / held LOD retest) and
pod-raschke-blindfold-breadth-div (two-low divergence). Stated change: a three-push structure with shrinking
momentum, with no range-position or breadth requirement. Close relative: pod-three-push-deceleration-low-long
(Tradeciety three drives: L3 = session low, volume decline, EMA9 trigger, H2 target); this one uses RSI divergence,
no session-low or volume rule, and a nearer-of target - checked with the duplicate scorer.
Rules (plain English, 5-minute bars, same session only):
  Swing low = a bar whose low is <= the lows of the 2 bars on each side; known only once the 2 bars after it closed.
  1. The last three confirmed swing lows L1 > L2 > L3, each at least 0.05 x atr_d below the previous one; L1 lies
     6-30 bars before the decision bar.
  2. Waning push: (swing high between L2 and L3) - L3 < (swing high between L1 and L2) - L2, and RSI(14) at the L3
     bar > RSI(14) at the L2 bar.
  3. spy_fo > -0.5% (not a bear trend day).
  4. Trigger: the first close above the high of the L3 bar once L3 is confirmed, within 6 bars of L3, bar close
     10:30-14:30.
  Entry: that close. Stop (GEOM S): L3 - 0.05 x atr_d. Target: the swing high between L1 and L2 (the second push's
  top) or VWAP, whichever is nearer above the entry; skip if < 0.8R away. Flat 15:55.
Pre-declared readings: a close above the L3 bar's high on the bar right after L3 (before L3 is confirmed) is not
counted, as it would need lookahead; '6-30 bars' is read as the distance from L1 to the decision bar. No tweak used.
No tuning on valid.
Costs per config/default.yaml (applied by the scorer). Only bars up to the decision bar are used.
Educational only - not financial advice."""
SIDE = "long"
GEOM = "S"
WINDOW = (1030, 1430)
CONTEXT = ["spy_fo"]
LAYERS = ["three lower swing lows (>= 0.05 ATR apart) in 6-30 bars", "push 3 drop < push 2 drop, RSI(L3) > RSI(L2)",
          "spy_fo > -0.5", "first close above the L3 bar high within 6 bars, 10:30-14:30",
          "stop L3 - 0.05 ATR, target nearer of push-2 top / VWAP (>= 0.8R)"]

import sys
from pathlib import Path

import numba
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


@numba.njit(cache=False)
def _scan(st, h, l, c, atr, rsi, vwap, sfo):
    n = len(c)
    m = np.zeros(n, np.bool_)
    stop = np.full(n, np.nan)
    tgt = np.full(n, np.nan)
    piv = np.zeros(n, np.int64)
    npiv = 0
    gs = 0
    for i in range(n):
        if st[i]:
            gs = i
            npiv = 0
        j = i - 2
        if j - 2 >= gs:
            if l[j] <= l[j - 1] and l[j] <= l[j - 2] and l[j] <= l[j + 1] and l[j] <= l[j + 2]:
                if not (npiv > 0 and piv[npiv - 1] >= j - 2 and l[piv[npiv - 1]] == l[j]):
                    piv[npiv] = j
                    npiv += 1
        if npiv < 3:
            continue
        L1 = piv[npiv - 3]
        L2 = piv[npiv - 2]
        L3 = piv[npiv - 1]
        if i - L1 < 6 or i - L1 > 30 or i - L3 > 6 or i < L3 + 2:
            continue
        a = atr[i]
        if not (l[L2] <= l[L1] - 0.05 * a and l[L3] <= l[L2] - 0.05 * a):
            continue
        if not (c[i] > h[L3]):
            continue
        first = True
        for t in range(L3 + 2, i):
            if c[t] > h[L3]:
                first = False
                break
        if not first:
            continue
        ha = -1e18
        for t in range(L1 + 1, L2):
            if h[t] > ha:
                ha = h[t]
        hb = -1e18
        for t in range(L2 + 1, L3):
            if h[t] > hb:
                hb = h[t]
        if ha < -1e17 or hb < -1e17:
            continue
        if not ((hb - l[L3]) < (ha - l[L2])):
            continue
        if not (rsi[L3] > rsi[L2]):
            continue
        if not (sfo[i] > -0.5):
            continue
        sp = l[L3] - 0.05 * a
        r = c[i] - sp
        if not (r > 0):
            continue
        tg = np.inf
        if ha > c[i]:
            tg = ha
        if vwap[i] > c[i] and vwap[i] < tg:
            tg = vwap[i]
        if not np.isfinite(tg) or (tg - c[i]) < 0.8 * r:
            continue
        m[i] = True
        stop[i] = sp
        tgt[i] = tg
    return m, stop, tgt


def mask(df) -> np.ndarray:
    _ST.clear()
    z = np.zeros(len(df), dtype=bool)
    if not len(df) or "spy_fo" not in df:
        return z
    k = _key(df)
    tod = df["tod"].to_numpy(np.int64)
    c = _f(df, "close")
    with np.errstate(invalid="ignore", divide="ignore"):
        vwap = c / (1 + _f(df, "vwapDistPct") / 100)
        m, stop, tgt = _scan(_start(k), _f(df, "high"), _f(df, "low"), c, _f(df, "atr_d"), _f(df, "rsi"), vwap,
                             _f(df, "spy_fo"))
        m &= (tod >= WINDOW[0]) & (tod <= WINDOW[1])
    _ST[id(df)] = (stop, tgt)
    return np.asarray(m & np.isfinite(stop) & np.isfinite(tgt), dtype=bool)
