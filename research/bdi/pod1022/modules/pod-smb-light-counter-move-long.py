"""pod-smb-light-counter-move-long - Light-volume counter-move in a midday uptrend, resumption entry (LONG).

Source: SMB Trading Tip of the Week 'Discover the Information in the Counter Move $LULU' (Mike Bellafiore).
URL: https://www.smbtraining.com/blog/smb-trade-of-the-week-discover-the-information-in-the-counter-move-lulu

VARIANT of 'P: first pullback holding VWAP/EMA9 after a morning low' (failed) and R08 bull flag (failed). Stated change:
the key condition is counter-move volume vs impulse volume, midday window, no morning-low requirement.

No tweak used; values are the source's. Impulse / counter-move definition (fixed before scoring): H = the bar with the
highest high among bars i-12..i-1, required 3..7 bars before i (so 2-6 counter-move bars H+1..i-1); the impulse starts
at the lowest low among bars i-12..H (bar j); impulse = high_H - low_j.

Rules (plain English), decision bar i:
  1. Uptrend: emaDiff > 0.10%, close > VWAP, sma20_slope_pct > 0.
  2. Impulse: high_H - low_j >= 0.5 x daily ATR with mean volumeRatio over bars j..H >= 1.3.
  3. Counter-move (bars H+1..i-1, 2-6 bars): retraces 30-60% of the impulse (lowest low of those bars), mean
     volumeRatio <= 0.7 x the impulse mean; flow3 >= -0.2 at bar i.
  4. Trigger: close_i > high_{i-1} with volumeRatio_i >= 1.0.
  Entry: close_i, bar close 11:00-14:30, one per symbol-day. Stop (GEOM S): counter-move low - 0.03 x daily ATR.
  Target: high_H + 0.5 x impulse. Flat 15:55. Costs in (scorer).
Educational only - not financial advice."""
import numba
import numpy as np
import pandas as pd

SIDE = "long"
GEOM = "S"
WINDOW = (1100, 1430)
LAYERS = ["emaDiff > 0.10, close > VWAP, sma20_slope_pct > 0",
          "impulse in the last 12 bars >= 0.5 ATR, mean volumeRatio >= 1.3",
          "2-6 bar counter-move retracing 30-60%, mean volumeRatio <= 0.7 x impulse, flow3 >= -0.2",
          "close > high[i-1], volumeRatio >= 1.0", "stop counter low - 0.03 ATR, target impulse high + 0.5 x impulse",
          "11:00-14:30 ET"]

_STASH = {}


def _segments(df):
    k = pd.factorize(pd.Series(df["symbol"].astype(str).to_numpy()) + "|" + pd.Series(df["date"].astype(str).to_numpy()))[0]
    n = len(k)
    if n == 0:
        return np.zeros(0, np.int64), np.zeros(0, np.int64)
    b = np.flatnonzero(np.r_[True, k[1:] != k[:-1]])
    return b.astype(np.int64), np.r_[b[1:], n].astype(np.int64)


@numba.njit(cache=False)
def _kernel(b, e, tod, c, h, l, ed, vd, ss, vr, f3, atr, w0, w1):
    n = len(c)
    m = np.zeros(n, np.bool_)
    stop = np.full(n, np.nan)
    tgt = np.full(n, np.nan)
    for s in range(len(b)):
        i0, i1 = b[s], e[s]
        for i in range(i0 + 12, i1):
            if tod[i] < w0 or tod[i] > w1:
                continue
            a = atr[i]
            if not (a > 0 and ed[i] > 0.10 and vd[i] > 0 and ss[i] > 0 and f3[i] >= -0.2):
                continue
            if not (c[i] > h[i - 1] and vr[i] >= 1.0):
                continue
            H = i - 12
            for k in range(i - 12, i):
                if h[k] > h[H]:
                    H = k
            if i - H < 3 or i - H > 7:
                continue
            j = i - 12
            for k in range(i - 12, H + 1):
                if l[k] < l[j]:
                    j = k
            imp = h[H] - l[j]
            if not (imp >= 0.5 * a):
                continue
            mi = 0.0
            for k in range(j, H + 1):
                mi += vr[k]
            mi /= (H - j + 1)
            if not (mi >= 1.3):
                continue
            cl = 1e18
            mc = 0.0
            for k in range(H + 1, i):
                cl = min(cl, l[k])
                mc += vr[k]
            mc /= (i - H - 1)
            rt = (h[H] - cl) / imp
            if not (rt >= 0.30 and rt <= 0.60 and mc <= 0.7 * mi):
                continue
            sp = cl - 0.03 * a
            tp = h[H] + 0.5 * imp
            if sp < c[i] and tp > c[i]:
                m[i] = True
                stop[i] = sp
                tgt[i] = tp
    return m, stop, tgt


def compute(df):
    n = len(df)
    if n == 0:
        return np.zeros(n, bool), np.full(n, np.nan), np.full(n, np.nan)
    f = lambda k: df[k].to_numpy(float)
    b, e = _segments(df)
    return _kernel(b, e, df["tod"].to_numpy(np.int64), f("close"), f("high"), f("low"), f("emaDiff"),
                   f("vwapDistPct"), f("sma20_slope_pct"), f("volumeRatio"), f("flow3"), f("atr_d"),
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
