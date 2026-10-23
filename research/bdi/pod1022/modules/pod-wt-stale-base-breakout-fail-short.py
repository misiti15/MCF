"""pod-wt-stale-base-breakout-fail-short - Weak-volume breakout from a 30-minute base after a run fails below the base
low (SHORT).

Source: Warrior Trading - 'Red Day Lessons with Ross Cameron' + 'Understanding False Breakouts in Day Trading'.
URL: https://www.warriortrading.com/red-day-lessons-with-ross-cameron/

VARIANT of CWT14 failed-breakout shorts (levels PDH / OR) and GEN ORBfail specs. Stated changes: the level is an
intraday sideways base formed AFTER a run, the breakout is on WEAK volume, and the failure is a close below the base
LOW (not back below the broken level).

Rules (plain English), decision bar i (all bars at or before i, same symbol-day):
  1. Run into the base: at the base's first bar fromOpen >= +3%, and among the 6 bars before the base >= 2 up bars
     (close above the previous close - the frame has no open) with a range (high - low) >= 0.15 x daily ATR.
  2. Base: N >= 6 consecutive bars (searched N = 15 down to 6, the longest that passes is used) whose total range
     (max high - min low) <= 0.3 x daily ATR and whose closes are all above the session VWAP.
  3. Breakout: a bar j among the last 3 bars (i-3..i-1), the bar right after the base, with high > base high + 0.02 x
     daily ATR and volumeRatio < 1.5 (weak volume); no close below the base low between j and i-1.
  4. Trigger: close_i < base low while close_i is still >= 0.15 x daily ATR above the session VWAP.
  Entry: close_i, bar close 10:30-14:30. Stop (GEOM S): the highest high from the breakout bar to bar i + 0.02 x daily
  ATR. Target: session VWAP at entry. Flat 15:55. Costs in (scorer). No tweak used (all values as in the spec).
Educational only - not financial advice."""
import numba
import numpy as np
import pandas as pd

SIDE = "short"
GEOM = "S"
WINDOW = (1030, 1430)
CONTEXT = []
LAYERS = ["run: fromOpen >= 3% at base start, >= 2 up bars with range >= 0.15 ATR in the 6 bars before",
          "base >= 6 bars, range <= 0.3 ATR, all closes above VWAP",
          "breakout bar in the last 3 bars: high > base high + 0.02 ATR with volumeRatio < 1.5",
          "close < base low, still >= 0.15 ATR above VWAP",
          "stop breakout high + 0.02 ATR, target VWAP at entry", "10:30-14:30 ET"]

_STASH = {}


def _segments(df):
    k = pd.factorize(pd.Series(df["symbol"].astype(str).to_numpy()) + "|" + pd.Series(df["date"].astype(str).to_numpy()))[0]
    n = len(k)
    if n == 0:
        return np.zeros(0, np.int64), np.zeros(0, np.int64)
    b = np.flatnonzero(np.r_[True, k[1:] != k[:-1]])
    return b.astype(np.int64), np.r_[b[1:], n].astype(np.int64)


@numba.njit(cache=False)
def _kernel(b, e, tod, c, h, l, vw, vr, fo, atr, w0, w1):
    n = len(c)
    m = np.zeros(n, np.bool_)
    stop = np.full(n, np.nan)
    tgt = np.full(n, np.nan)
    for s in range(len(b)):
        i0, i1 = b[s], e[s]
        for i in range(i0 + 10, i1):
            if tod[i] < w0 or tod[i] > w1:
                continue
            a = atr[i]
            if not (a > 0 and c[i] >= vw[i] + 0.15 * a):
                continue
            found = False
            for j in range(i - 1, i - 4, -1):
                if found:
                    break
                if not (vr[j] < 1.5):
                    continue
                for N in range(15, 5, -1):
                    bs = j - N
                    if bs - 6 < i0 + 1:
                        continue
                    bh = -1e18
                    bl = 1e18
                    ok = True
                    for k in range(bs, j):
                        bh = max(bh, h[k])
                        bl = min(bl, l[k])
                        if not (c[k] > vw[k]):
                            ok = False
                            break
                    if not ok or bh - bl > 0.3 * a:
                        continue
                    if not (h[j] > bh + 0.02 * a):
                        continue
                    if not (c[i] < bl):
                        continue
                    fail = False
                    for k in range(j, i):
                        if c[k] < bl:
                            fail = True
                            break
                    if fail:
                        continue
                    if not (fo[bs] >= 3.0):
                        continue
                    up = 0
                    for k in range(bs - 6, bs):
                        if c[k] > c[k - 1] and h[k] - l[k] >= 0.15 * a:
                            up += 1
                    if up < 2:
                        continue
                    hh = -1e18
                    for k in range(j, i + 1):
                        hh = max(hh, h[k])
                    sp = hh + 0.02 * a
                    if sp > c[i] and vw[i] < c[i]:
                        m[i] = True
                        stop[i] = sp
                        tgt[i] = vw[i]
                        found = True
                        break
    return m, stop, tgt


def compute(df):
    n = len(df)
    if n == 0:
        return np.zeros(n, bool), np.full(n, np.nan), np.full(n, np.nan)
    f = lambda k: df[k].to_numpy(float)
    c = f("close")
    with np.errstate(invalid="ignore", divide="ignore"):
        vw = c / (1 + f("vwapDistPct") / 100)
    b, e = _segments(df)
    return _kernel(b, e, df["tod"].to_numpy(np.int64), c, f("high"), f("low"), vw, f("volumeRatio"), f("fromOpen"),
                   f("atr_d"), WINDOW[0], WINDOW[1])


def mask(df) -> np.ndarray:
    m, stop, tgt = compute(df)
    _STASH.clear()
    _STASH[id(df)] = (stop, tgt)
    return m


def _get(f):
    s = _STASH.get(id(f))
    if s is None or len(s[0]) != len(f):
        mask(f)
        s = _STASH[id(f)]
    return s


def stop_price(f, i):
    return float(_get(f)[0][i])


def target_price(f, i, stop):
    return float(_get(f)[1][i])
