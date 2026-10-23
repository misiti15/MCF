"""pod-wt-flat-top-poor-high-long - Flat-top / poor-high breakout: >= 3 flat touches of one level with rising lows, buy the break
(LONG). Config POOR (no leg; tail-less touches; level set >= 30 min ago; 11:00-15:00).

Source: Warrior Trading (Ross Cameron) 'Flat Top Breakout Pattern'; auction-market 'poor high = unfinished auction'
(LuxAlgo, MarketCalls; Trader Dante AMT video). Long mirror of pod-of-poor-extreme-break folded in.
URL: https://www.warriortrading.com/flat-top-breakout-pattern/

VARIANT of CWT12 coil under resistance (cwt-b-b4, failed), R07 HOD break (failed) and wi-intraday-vcp (idea). Stated
change: an explicit multi-touch flat top (>= 3 highs at one level, no tails) with rising lows, and a base-height target.

Pre-declared values inside the source ranges (no tuning): touch tolerance 0.05 x daily ATR (range 0.03-0.08), break
buffer 0.03 x daily ATR (0.02-0.05), trigger volumeRatio >= 1.4 (1.3-1.5).

Rules (plain English), decision bar i; the base is bars i-N..i-1 for the largest N in 4..15 that passes:
  1. Config WT: >= 3 up bars (close above the previous close) among the 12 bars before the base, and fromOpen >= +2%
     at bar i. (Config POOR, separate file: no leg; every touch bar has upper_wick < 0.25 and the first touch is
     >= 6 bars (30 min) before bar i.)
  2. L = max high of the base; >= 3 base bars have a high within 0.05 x daily ATR of L (no close above L by
     construction).
  3. Config WT only: L within 0.3% of a round number ($5 step >= $100, $1 >= $20, else $0.5 - the frame's
     dist_round_atr steps).
  4. The lowest low of the base's second half > the lowest low of its first half (rising lows); mean base
     volumeRatio < 1.
  5. Trigger: close_i > L + 0.03 x daily ATR, volumeRatio_i >= 1.4, spy_fo > 0.
  Entry: trigger close, 09:50-14:30 (POOR: 11:00-15:00). Stop (GEOM S): the second-half (last higher) low of the base
  - 0.02 x daily ATR. Target: L + base height (L - lowest base low). Flat 15:55. Costs in (scorer).
Educational only - not financial advice."""
import numba
import numpy as np
import pandas as pd

SIDE = "long"
GEOM = "S"
WINDOW = (1100, 1500)
CONFIG = "POOR"
CONTEXT = ["spy_fo"]
LAYERS = ["config POOR: touch bars upper_wick < 0.25, first touch >= 30 min before the trigger",
          ">= 3 highs within 0.05 ATR of the base high (base 4-15 bars)", "rising lows, mean base volumeRatio < 1",
          "close > L + 0.03 ATR, volumeRatio >= 1.4, spy_fo > 0",
          "stop 2nd-half base low - 0.02 ATR, target L + base height", "11:00-15:00 ET"]

_STASH = {}


def _segments(df):
    k = pd.factorize(pd.Series(df["symbol"].astype(str).to_numpy()) + "|" + pd.Series(df["date"].astype(str).to_numpy()))[0]
    n = len(k)
    if n == 0:
        return np.zeros(0, np.int64), np.zeros(0, np.int64)
    b = np.flatnonzero(np.r_[True, k[1:] != k[:-1]])
    return b.astype(np.int64), np.r_[b[1:], n].astype(np.int64)


@numba.njit(cache=False)
def _kernel(b, e, tod, c, h, l, uw, vr, fo, spy, atr, cfg, w0, w1):
    n = len(c)
    m = np.zeros(n, np.bool_)
    stop = np.full(n, np.nan)
    tgt = np.full(n, np.nan)
    for s in range(len(b)):
        i0, i1 = b[s], e[s]
        for i in range(i0 + 4, i1):
            if tod[i] < w0 or tod[i] > w1:
                continue
            if not (spy[i] > 0 and vr[i] >= 1.4):
                continue
            a = atr[i]
            if cfg == 0 and not (fo[i] >= 2.0):
                continue
            for N in range(15, 3, -1):
                st = i - N
                if st < i0:
                    continue
                if cfg == 0 and st - 12 < i0 + 1:
                    continue
                L = -1e18
                for k in range(st, i):
                    L = max(L, h[k])
                if not (c[i] > L + 0.03 * a):
                    continue
                touches = 0
                first = -1
                okw = True
                for k in range(st, i):
                    if h[k] >= L - 0.05 * a:
                        touches += 1
                        if first < 0:
                            first = k
                        if uw[k] >= 0.25:
                            okw = False
                if touches < 3:
                    continue
                if cfg == 1 and (not okw or i - first < 6):
                    continue
                half = N // 2
                lo1 = 1e18
                lo2 = 1e18
                mv = 0.0
                for k in range(st, i):
                    if k < st + half:
                        lo1 = min(lo1, l[k])
                    else:
                        lo2 = min(lo2, l[k])
                    mv += vr[k]
                if not (lo2 > lo1 and mv / N < 1.0):
                    continue
                if cfg == 0:
                    up = 0
                    for k in range(st - 12, st):
                        if c[k] > c[k - 1]:
                            up += 1
                    if up < 3:
                        continue
                    stp = 0.5 if L < 20 else (1.0 if L < 100 else 5.0)
                    rn = np.round(L / stp) * stp
                    if abs(L - rn) > 0.003 * L:
                        continue
                sp = lo2 - 0.02 * a
                tp = L + (L - lo1)
                if sp < c[i] and tp > c[i]:
                    m[i] = True
                    stop[i] = sp
                    tgt[i] = tp
                    break
    return m, stop, tgt


def compute(df):
    n = len(df)
    if n == 0 or "spy_fo" not in df:
        return np.zeros(n, bool), np.full(n, np.nan), np.full(n, np.nan)
    f = lambda k: df[k].to_numpy(float)
    b, e = _segments(df)
    return _kernel(b, e, df["tod"].to_numpy(np.int64), f("close"), f("high"), f("low"), f("upper_wick"),
                   f("volumeRatio"), f("fromOpen"), f("spy_fo"), f("atr_d"), 0 if CONFIG == "WT" else 1,
                   WINDOW[0], WINDOW[1])


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
