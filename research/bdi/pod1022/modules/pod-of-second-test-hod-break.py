"""pod-of-second-test-hod-break - Second test of a failed HOD: go WITH the break (LONG).

Source: NexusFi 'Failed Auction' concept page; Trader Dante swing-failure-pattern (SFP) material.
URL: https://nexusfi.com/a/concepts/failed-auction

VARIANT of bdi1014-cwt14-sar (reverse into the break after a CWT14 fade's stop fills). Stated change: the level is the
intraday HOD, no prior trade is needed, and entry is the break on the SECOND test after a recorded first failure.
Different from pod-smb-second-chance-hod-retest (that one buys a held retest after a successful break).

Rules (plain English), decision bar i:
  1. Failure bar F, at least 6 bars before i, closing after 10:00: its high poked above the then-HOD (the high of day
     as of bar F-1) and it closed back below that HOD, with upper_wick >= 0.5. The most recent such F is used.
  2. F's high stays the level: no bar between F and i made a high more than 0.03 x atr_d above it, and no bar
     between F and i closed above F high + 0.03 x atr_d (bar i is the first break).
  3. Second test: some bar after F up to i has a high within 0.05 x atr_d of F's high (the trigger bar may be it).
  4. Trigger: close_i > F high + 0.03 x atr_d with volumeRatio >= 1.2; close_i > session VWAP; breadth >= 0.55.
  5. The pullback between F and the trigger held above VWAP: every bar after F up to i-1 has its low at or above
     its own session VWAP.
  Entry: the trigger close. Stop (GEOM S): the trigger-bar low. Target: 1 x the entry-to-stop risk (the source's 1R
  option; the t1s05 / holdtr alternatives are not scored - one configuration). Flat 15:55. Bar close 10:30-14:30.
  No tweak used. Only bars up to the decision bar are used. Costs in (scorer, config/default.yaml).
Educational only - not financial advice."""
SIDE = "long"
GEOM = "S"
WINDOW = (1030, 1430)
CONTEXT = ["breadth"]
LAYERS = ["failure bar F >= 6 bars ago after 10:00: poke above HOD, close back below, upper_wick >= 0.5",
          "retest high within 0.05 ATR of F high, F high still the level", "close > F high + 0.03 ATR, volumeRatio >= 1.2",
          "close > VWAP, breadth >= 0.55, pullback lows held VWAP", "stop trigger low, target 1x risk", "10:30-14:30 ET"]

import numba
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
    return np.r_[True, k[1:] != k[:-1]] if len(k) else np.zeros(0, bool)


def _lag(x, k, n=1):
    """x from n bars earlier in the same symbol-day (NaN across a day boundary)."""
    x = np.asarray(x, float)
    p = np.full(len(x), np.nan)
    if len(x) > n:
        p[n:] = x[:-n]
        p[n:][k[n:] != k[:-n]] = np.nan
    return p


def _gcum(x, k):
    """Inclusive running sum within each symbol-day."""
    x = np.asarray(x, float)
    cs = np.cumsum(x)
    st = _start(k)
    base = (cs - x)[st]
    return cs - base[np.cumsum(st) - 1]


def _at(x, k, tod, T):
    """Value of x on the bar closing at T, broadcast to its symbol-day. Use only on rows with tod >= T."""
    gv = np.full(int(k.max()) + 1 if len(k) else 1, np.nan)
    sel = tod == T
    gv[k[sel]] = np.asarray(x, float)[sel]
    return gv[k]


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


def _segments(k):
    n = len(k)
    if n == 0:
        return np.zeros(0, np.int64), np.zeros(0, np.int64)
    b = np.flatnonzero(_start(k))
    return b.astype(np.int64), np.r_[b[1:], n].astype(np.int64)


@numba.njit(cache=False)
def _kernel(b, e, tod, c, h, l, hod, vw, uw, vr, br, atr, w0, w1):
    n = len(c)
    m = np.zeros(n, np.bool_)
    stop = np.full(n, np.nan)
    tgt = np.full(n, np.nan)
    for s in range(len(b)):
        i0, i1 = b[s], e[s]
        for i in range(i0 + 7, i1):
            if tod[i] < w0 or tod[i] > w1:
                continue
            a = atr[i]
            if not (a > 0 and vr[i] >= 1.2 and c[i] > vw[i] and br[i] >= 0.55):
                continue
            # most recent failure bar F with i - F >= 6
            for F in range(i - 6, i0, -1):
                if tod[F] <= 1000:
                    break
                L = hod[F - 1]
                if not (h[F] > L and c[F] < L and uw[F] >= 0.5):
                    continue
                hf = h[F]
                if not (c[i] > hf + 0.03 * a):
                    break
                ok = True
                tested = h[i] >= hf - 0.05 * a
                for q in range(F + 1, i):
                    if h[q] > hf + 0.03 * a or c[q] > hf + 0.03 * a or l[q] < vw[q]:
                        ok = False
                        break
                    if h[q] >= hf - 0.05 * a:
                        tested = True
                if ok and tested and l[i] < c[i]:
                    m[i] = True
                    stop[i] = l[i]
                    tgt[i] = c[i] + (c[i] - l[i])
                break
    return m, stop, tgt


def mask(df) -> np.ndarray:
    n = len(df)
    _ST.clear()
    if not n or "breadth" not in df:
        return np.zeros(n, dtype=bool)
    k = _key(df)
    c, atr = _f(df, "close"), _f(df, "atr_d")
    with np.errstate(invalid="ignore", divide="ignore"):
        hod = c + _f(df, "dist_hod_atr") * atr
        vw = c / (1 + _f(df, "vwapDistPct") / 100)
    b, e = _segments(k)
    m, stop, tgt = _kernel(b, e, df["tod"].to_numpy(np.int64), c, _f(df, "high"), _f(df, "low"), hod, vw,
                           _f(df, "upper_wick"), _f(df, "volumeRatio"), _f(df, "breadth"), atr, WINDOW[0], WINDOW[1])
    _ST[id(df)] = (stop, tgt)
    return np.asarray(m, dtype=bool)


def target_price(f, i, stop):
    return _stash_get(f, i, 1)
