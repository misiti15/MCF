"""pod-smb-held-floor-triple-bottom-long - Held-floor triple bottom: three tests of a flat low hold, long the neckline
break (LONG).

Source: SMB Capital PlayBook / SMB YouTube tape-reading reviews (a buyer holds a price; mirror of the 'stuffed' triple
top). Taken from SMB material already known; the web was unavailable this round.
URL: https://www.youtube.com/@smbcapital

VARIANT of pod-smb-stuffed-triple-top-neckline (opposite side) and the inverse of pod-smb-bouncy-ball-support-break:
here the floor HOLDS.

Rules (plain English), decision bar i:
  1. Floor F = the lowest low of the bars closing 10:30-14:00 before bar i. Swing low at bar k: low_k < low_{k-1} and
     low_k <= low_{k+1} (k+1 <= i, so it is confirmed). Tests = swing lows closing 10:30-14:00 with low within 0.10 x
     daily ATR of F, picked in order with at least 2 bars between picks (index gap >= 3). >= 3 tests.
  2. No 5-min close below F - 0.05 ATR from 10:30 to bar i (implied by F being the lowest low; checked anyway).
  3. volumeRatio at the 3rd (last) test <= volumeRatio at the 1st test (sellers drying up).
  4. Counter-trend: the close of bar i is still >= 0.5 x daily ATR below today's open (pre-declared reading: checked
     on the decision bar).
  Trigger: neckline N = the highest high between the first and the last test; close_i > N and close_{i-1} <= N,
  bar i after the last test.
  Entry: the scorer enters at close_i, bar close 10:45-14:30 ET, one per symbol-day.
  Stop (GEOM S): F - 0.10 ATR. Target: VWAP; 1.5R when VWAP is less than 1R above the entry. The source's 60-minute
  time stop is not supported by the scorer (it holds to the stop, target or 15:55). Costs in (scorer).
No tweak used; thresholds are the idea's.
Educational only - not financial advice."""
import numba
import numpy as np
import pandas as pd

SIDE = "long"
GEOM = "S"
WINDOW = (1045, 1430)
LAYERS = [">= 3 swing lows 10:30-14:00 within 0.10 ATR of the floor, >= 2 bars apart",
          "no close below floor - 0.05 ATR", "volumeRatio 3rd test <= 1st test", "close >= 0.5 ATR below the open",
          "close crosses above the neckline", "stop floor - 0.10 ATR, target VWAP or 1.5R", "10:45-14:30 ET"]

_STASH = {}


def _segments(df):
    k = pd.factorize(pd.Series(df["symbol"].astype(str).to_numpy()) + "|" + pd.Series(df["date"].astype(str).to_numpy()))[0]
    n = len(k)
    if n == 0:
        return np.zeros(0, np.int64), np.zeros(0, np.int64)
    b = np.flatnonzero(np.r_[True, k[1:] != k[:-1]])
    return b.astype(np.int64), np.r_[b[1:], n].astype(np.int64)


@numba.njit(cache=False)
def _kernel(b, e, tod, c, h, l, fo, vr, vd, atr, w0, w1):
    n = len(c)
    m = np.zeros(n, np.bool_)
    stop = np.full(n, np.nan)
    tgt = np.full(n, np.nan)
    tests = np.zeros(200, np.int64)
    for s in range(len(b)):
        i0, i1 = b[s], e[s]
        a = atr[i0]
        if not (a > 0):
            continue
        for i in range(i0 + 2, i1):
            if tod[i] < w0 or tod[i] > w1:
                continue
            op = c[i] / (1.0 + fo[i] / 100.0)
            if not (op - c[i] >= 0.5 * a):
                continue
            F = 1e18
            cmin = 1e18
            for k in range(i0, i):
                if tod[k] >= 1030 and tod[k] <= 1400:
                    if l[k] < F:
                        F = l[k]
                if tod[k] >= 1030 and c[k] < cmin:
                    cmin = c[k]
            if not (F < 1e17) or cmin < F - 0.05 * a:
                continue
            nt = 0
            last = -10
            for k in range(i0 + 1, i):
                if tod[k] < 1030 or tod[k] > 1400:
                    continue
                if not (l[k] < l[k - 1] and l[k] <= l[k + 1] and l[k] <= F + 0.10 * a):
                    continue
                if k - last >= 3:
                    tests[nt] = k
                    nt += 1
                    last = k
            if nt < 3:
                continue
            k1, k3 = tests[0], tests[nt - 1]
            if not (vr[k3] <= vr[k1]):
                continue
            N = -1e18
            for k in range(k1, k3 + 1):
                if h[k] > N:
                    N = h[k]
            if not (i > k3 and c[i] > N and c[i - 1] <= N):
                continue
            sp = F - 0.10 * a
            R = c[i] - sp
            if not (R > 0):
                continue
            vw = c[i] / (1.0 + vd[i] / 100.0)
            t = vw if vw - c[i] >= R else c[i] + 1.5 * R
            m[i] = True
            stop[i] = sp
            tgt[i] = t
    return m, stop, tgt


def compute(df):
    n = len(df)
    if n == 0:
        return np.zeros(n, bool), np.full(n, np.nan), np.full(n, np.nan)
    f = lambda k: df[k].to_numpy(float)
    b, e = _segments(df)
    return _kernel(b, e, df["tod"].to_numpy(np.int64), f("close"), f("high"), f("low"), f("fromOpen"),
                   f("volumeRatio"), f("vwapDistPct"), f("atr_d"), WINDOW[0], WINDOW[1])


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
