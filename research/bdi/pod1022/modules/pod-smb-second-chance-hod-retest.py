"""pod-smb-second-chance-hod-retest - Second-Chance scalp: HOD breakout, shallow retest of the old HOD holds, two-bar-high
reclaim (LONG).

Source: SMB Capital Scalp Radar '2nd Chance Scalp' (Scribd description; SMB Scalp Radar page).
URL: https://smbtraining.com/blog/smb-scalp-radar

VARIANT of R07 HOD break (failed) and R17 PDH retest (failed). Stated change: the level is the broken intraday HOD
(not PDH) and entry waits for a retest that holds plus a two-bar-high reclaim.

EMA9: the continuous 5-minute EMA9 behind the frame's emaDiff, recovered exactly (seeds solved from the day's first two
rows; same method as pod-bbt-parabolic-ema9-snapback-short). The then-HOD L of the breakout bar k is the running high
of day as of bar k-1 (close_{k-1} + dist_hod_atr_{k-1} x atr_d, which includes the pre-09:50 bars).

Rules (plain English), decision bar i:
  1. Breakout: a bar k 3-10 bars before i closed above the then-HOD L (the HOD as of bar k-1) with volumeRatio_k >= 1.5
     (the most recent such k is used).
  2. Retest: some bar after k up to i has low <= L + 0.10 x daily ATR, and no bar after k up to i closed below
     L - 0.05 x daily ATR.
  3. close_i > VWAP_i, EMA9_i > VWAP_i, spy_fo > -0.2%.
  4. Trigger: close_i > max(high_{i-1}, high_{i-2}).
  Entry: close_i, bar close 10:15-14:30, one per symbol-day. Stop (GEOM S): min(retest low, L - 0.10 x daily ATR),
  the retest low = the lowest low after k up to i. Target: new HOD + (new HOD - L), new HOD = high of day at bar i.
  Flat 15:55. Costs in (scorer). No tweak used.
Educational only - not financial advice."""
import numba
import numpy as np
import pandas as pd

SIDE = "long"
GEOM = "S"
WINDOW = (1015, 1430)
CONTEXT = ["spy_fo"]
LAYERS = ["breakout 3-10 bars ago: close > then-HOD with volumeRatio >= 1.5",
          "retest low <= old HOD + 0.10 ATR, no close below old HOD - 0.05 ATR",
          "close > VWAP, EMA9 > VWAP, spy_fo > -0.2%", "close > max(high_{i-1}, high_{i-2})",
          "stop min(retest low, old HOD - 0.10 ATR), target new HOD + (new HOD - old HOD)", "10:15-14:30 ET"]

_STASH = {}


def _segments(df):
    k = pd.factorize(pd.Series(df["symbol"].astype(str).to_numpy()) + "|" + pd.Series(df["date"].astype(str).to_numpy()))[0]
    n = len(k)
    if n == 0:
        return np.zeros(0, np.int64), np.zeros(0, np.int64)
    b = np.flatnonzero(np.r_[True, k[1:] != k[:-1]])
    return b.astype(np.int64), np.r_[b[1:], n].astype(np.int64)


@numba.njit(cache=False)
def _ema9(b, e, c, ed):
    out = np.full(len(c), np.nan)
    a9, a21 = 0.2, 2.0 / 22.0
    for s in range(len(b)):
        i0, i1 = b[s], e[s]
        if i1 - i0 < 2:
            continue
        d0, d1 = ed[i0] / 100.0, ed[i0 + 1] / 100.0
        den = (1 - a9) * (1 + d0) - (1 - a21) * (1 + d1)
        if den == 0.0 or d0 != d0 or d1 != d1:
            continue
        E = (a21 * c[i0 + 1] * (1 + d1) - a9 * c[i0 + 1]) / den
        e9 = (1 + d0) * E
        for i in range(i0 + 1, i1):
            e9 = a9 * c[i] + (1 - a9) * e9
            out[i] = e9
    return out


@numba.njit(cache=False)
def _kernel(b, e, tod, c, h, l, hod, vw, e9, vr, spy, atr, w0, w1):
    n = len(c)
    m = np.zeros(n, np.bool_)
    stop = np.full(n, np.nan)
    tgt = np.full(n, np.nan)
    for s in range(len(b)):
        i0, i1 = b[s], e[s]
        for i in range(i0 + 11, i1):
            if tod[i] < w0 or tod[i] > w1:
                continue
            a = atr[i]
            if not (a > 0 and c[i] > vw[i] and e9[i] > vw[i] and spy[i] > -0.2):
                continue
            if not (c[i] > max(h[i - 1], h[i - 2])):
                continue
            for k in range(i - 3, i - 11, -1):
                L = hod[k - 1]
                if not (c[k] > L and vr[k] >= 1.5):
                    continue
                lo = 1e18
                bad = False
                for q in range(k + 1, i + 1):
                    lo = min(lo, l[q])
                    if c[q] < L - 0.05 * a:
                        bad = True
                        break
                if bad or not (lo <= L + 0.10 * a):
                    break           # the most recent breakout decides
                sp = min(lo, L - 0.10 * a)
                nh = hod[i]
                tp = nh + (nh - L)
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
    c, atr = f("close"), f("atr_d")
    with np.errstate(invalid="ignore", divide="ignore"):
        vw = c / (1 + f("vwapDistPct") / 100)
        hod = c + f("dist_hod_atr") * atr
    b, e = _segments(df)
    e9 = _ema9(b, e, c, f("emaDiff"))
    return _kernel(b, e, df["tod"].to_numpy(np.int64), c, f("high"), f("low"), hod, vw, e9, f("volumeRatio"),
                   f("spy_fo"), atr, WINDOW[0], WINDOW[1])


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
