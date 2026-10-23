"""pod-wt-ascending-triangle-midday-long - Ascending triangle (higher lows into a flat top), midday break (LONG).

Source: Warrior Trading / Ross Cameron, flat-top breakout and ascending-triangle pattern lessons (warriortrading.com
flat-top-breakout-pattern; YouTube). Not re-fetched this round.
URL: https://www.warriortrading.com/flat-top-breakout-pattern/

VARIANT of pod-wt-flat-top-poor-high-long and pod-wt-flat-top-roundnum-long. Stated changes: the setup needs a
rising-lows condition (>= 3 higher swing lows converging on the top), the resistance does not have to be the HOD or a
round number, and it runs only midday (11:30-14:30) as a compression play.

Rules (plain English), decision bar i; the window is bars i-N..i-1, N scanned from 24 down to 8 (pre-declared: the
longest window that passes is used; the source gives no single length):
  1. Resistance T = max high of the window, touched >= 3 times (bars with high within 0.05 x atr_d of T), counting
     only touches that are >= 3 bars apart from the previous counted touch (index gap >= 4).
  2. Rising lows: the 3 most recent 3-bar pivot lows inside the window (low below both neighbours; the right
     neighbour is at most bar i-1) are strictly rising, and the last one is within 0.35 x atr_d of T.
  3. Mean volumeRatio over the window <= 0.9, and the window range (T - lowest window low) <= 0.6 x atr_d.
  4. Bar i: close > T + 0.02 x atr_d, volumeRatio >= 1.5, close > session VWAP, sma20_slope_pct >= 0.
  5. breadth >= 0.45 (context).
  Entry: close_i, bar close 11:30-14:30. Stop (GEOM S): the last rising pivot low - 0.02 x atr_d.
  Target: T + triangle height (T - first pivot low), else flat 15:55. Costs in (scorer, config/default.yaml).
No tweak made. Only bars up to the decision bar are used.
Educational only - not financial advice."""
import numba
import numpy as np
import pandas as pd

SIDE = "long"
GEOM = "S"
WINDOW = (1130, 1430)
CONTEXT = ["breadth"]
LAYERS = ["flat top T touched >= 3x (0.05 ATR, >= 3 bars apart) over 8-24 bars",
          "3 rising pivot lows, last within 0.35 ATR of T", "window mean volumeRatio <= 0.9, range <= 0.6 ATR",
          "close > T + 0.02 ATR, volumeRatio >= 1.5, above VWAP, sma20 slope >= 0", "breadth >= 0.45",
          "stop last pivot low - 0.02 ATR, target T + height", "11:30-14:30"]

_ST = {}


def _segments(df):
    k = pd.factorize(pd.Series(df["symbol"].astype(str).to_numpy()) + "|" + pd.Series(df["date"].astype(str).to_numpy()))[0]
    n = len(k)
    if n == 0:
        return np.zeros(0, np.int64), np.zeros(0, np.int64)
    b = np.flatnonzero(np.r_[True, k[1:] != k[:-1]])
    return b.astype(np.int64), np.r_[b[1:], n].astype(np.int64)


@numba.njit(cache=False)
def _kern(b, e, tod, c, h, l, vr, vw, slope, br, atr, w0, w1):
    n = len(c)
    m = np.zeros(n, np.bool_)
    stop = np.full(n, np.nan)
    tgt = np.full(n, np.nan)
    for s in range(len(b)):
        i0, i1 = b[s], e[s]
        for i in range(i0 + 8, i1):
            if tod[i] < w0 or tod[i] > w1:
                continue
            a = atr[i]
            if not (a > 0 and vr[i] >= 1.5 and c[i] > vw[i] and slope[i] >= 0 and br[i] >= 0.45):
                continue
            for N in range(24, 7, -1):
                st = i - N
                if st < i0:
                    continue
                T = -1e18
                lo = 1e18
                mv = 0.0
                for k in range(st, i):
                    T = max(T, h[k])
                    lo = min(lo, l[k])
                    mv += vr[k]
                if not (c[i] > T + 0.02 * a):
                    continue
                if mv / N > 0.9 or T - lo > 0.6 * a:
                    continue
                touches = 0
                last = -100
                for k in range(st, i):
                    if h[k] >= T - 0.05 * a and k - last >= 4:
                        touches += 1
                        last = k
                if touches < 3:
                    continue
                # 3 most recent pivot lows in the window (k-1 >= st, k+1 <= i-1)
                p3 = -1
                p2 = -1
                p1 = -1
                cnt = 0
                for k in range(i - 2, st, -1):
                    if l[k] < l[k - 1] and l[k] < l[k + 1]:
                        if cnt == 0:
                            p3 = k
                        elif cnt == 1:
                            p2 = k
                        else:
                            p1 = k
                        cnt += 1
                        if cnt == 3:
                            break
                if cnt < 3:
                    continue
                if not (l[p1] < l[p2] and l[p2] < l[p3]):
                    continue
                if T - l[p3] > 0.35 * a:
                    continue
                sp = l[p3] - 0.02 * a
                tp = T + (T - l[p1])
                if sp < c[i] and tp > c[i]:
                    m[i] = True
                    stop[i] = sp
                    tgt[i] = tp
                    break
    return m, stop, tgt


def mask(df) -> np.ndarray:
    _ST.clear()
    n = len(df)
    if n == 0 or "breadth" not in df:
        return np.zeros(n, dtype=bool)
    f = lambda k: df[k].to_numpy(float)
    c = f("close")
    vw = c / (1 + f("vwapDistPct") / 100)
    b, e = _segments(df)
    m, stop, tgt = _kern(b, e, df["tod"].to_numpy(np.int64), c, f("high"), f("low"), f("volumeRatio"), vw,
                         f("sma20_slope_pct"), f("breadth"), f("atr_d"), WINDOW[0], WINDOW[1])
    _ST[id(df)] = (stop, tgt)
    return np.asarray(m, dtype=bool)


def _get(f):
    s = _ST.get(id(f))
    if s is None or len(s[0]) != len(f):
        mask(f)
        s = _ST[id(f)]
    return s


def stop_price(f, i):
    return float(_get(f)[0][i])


def target_price(f, i, stop):
    return float(_get(f)[1][i])
