"""pod-wt-abcd-buy-at-c-dtarget-long - ABCD bought at the C turn above VWAP, target D = C + (B - A) (LONG). Config D-target.

Source: Warrior Trading 'ABCD Pattern' article + Andrew Aziz, How to Day Trade for a Living (buy close to point C).
URL: https://www.warriortrading.com/abcd-pattern/

VARIANT of bdi-reddit-abcd (idea: buy the BREAK OF B) and ART fib618 touch (failed). Stated changes: entry moved to the
C turn, C must hold VWAP, first target is B. Separate configs (separate files): D target = C + (B - A)
(pod-wt-abcd-buy-at-c-dtarget-long) and the short mirror (pod-wt-abcd-sell-at-c-short).

EMA9: the true continuous 5-minute EMA9 recovered exactly from emaDiff (EMA9 = EMA21 x (1 + emaDiff); seeds solved
from the 09:50 and 09:55 rows), known from 09:55.

Rules (plain English), every value from bars up to and including the decision bar i:
  1. A = the low of day, set on a frame bar (09:50 or later; a low set before 09:50 has no bar count, so it does not
     qualify). B = the highest high after A; B - A >= 0.6 x daily ATR and B was reached <= 8 bars after A.
  2. C = the lowest low since B, >= 2 bars after B, retracing 38.2-61.8% of AB.
  3. C low >= session VWAP (at the C bar) - 0.05 x daily ATR; mean volumeRatio on B+1..C < mean on A..B.
  4. Trigger: the first bar after C with close > high_{i-1} and close > EMA9; close <= B - 0.3 x (B - A).
  A new low of day re-anchors A; a new high above B re-anchors B (and C).
  Entry: close, 10:00-12:30. Stop (GEOM S): C low - 0.03 x daily ATR. Target (this config): D = C + (B - A). Flat 15:55. Costs in (scorer).
  No tweak used.
Educational only - not financial advice."""
import numba
import numpy as np
import pandas as pd

SIDE = "long"
GEOM = "S"
WINDOW = (1000, 1230)
TARGET = "D"
CONTEXT = []
LAYERS = ["A = in-frame LOD, B - A >= 0.6 ATR within 8 bars", "C >= 2 bars after B, 38.2-61.8% retrace",
          "C holds VWAP - 0.05 ATR, lighter volume on BC", "close > prior high and > EMA9, close <= B - 0.3 AB",
          "stop C - 0.03 ATR, target D = C + (B - A)", "10:00-12:30 ET"]

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
    """Continuous EMA9 recovered from emaDiff; NaN on each day's first row (needs the second row to solve)."""
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
def _kernel(b, e, tod, c, h, l, ext, vw, e9, vr, atr, sg, tmode, w0, w1):
    """sg = +1 long (A = LOD, B = high after A) / -1 short (A = HOD, B = low after A). Prices are multiplied by sg so
    one long-form loop serves both sides: x = sg*price, with highs/lows swapped for the short."""
    n = len(c)
    m = np.zeros(n, np.bool_)
    stop = np.full(n, np.nan)
    tgt = np.full(n, np.nan)
    for s in range(len(b)):
        i0, i1 = b[s], e[s]
        ja = -1
        jb = -1
        jc = -1
        for i in range(i0, i1):
            # long-form views: lo = favourable-side low, hi = high
            lo_i = l[i] if sg > 0 else -h[i]
            hi_i = h[i] if sg > 0 else -l[i]
            ex = ext[i] if sg > 0 else -ext[i]       # running LOD (long) / -HOD (short)
            if lo_i <= ex + 1e-9 * abs(c[i]):
                if ja < 0 or lo_i < (l[ja] if sg > 0 else -h[ja]):
                    ja = i
                    jb = -1
                    jc = -1
                    continue
            if ja < 0:
                continue
            if jb < 0 or hi_i > (h[jb] if sg > 0 else -l[jb]):
                jb = i
                jc = -1
                continue
            A = l[ja] if sg > 0 else -h[ja]
            B = h[jb] if sg > 0 else -l[jb]
            # trigger check uses C as known before bar i
            if jc >= 0 and tod[i] >= w0 and tod[i] <= w1 and i > jc:
                a = atr[i]
                C = l[jc] if sg > 0 else -h[jc]
                ab = B - A
                x_c = c[i] * sg
                x_ph = h[i - 1] if sg > 0 else -l[i - 1]
                x_e9 = e9[i] * sg
                vwc = vw[jc] * sg
                ok = ab >= 0.6 * a and jb - ja <= 8 and jc - jb >= 2
                if ok:
                    rt = (B - C) / ab
                    ok = rt >= 0.382 and rt <= 0.618
                if ok:
                    ok = C >= vwc - 0.05 * a
                if ok:
                    v1 = 0.0
                    for k in range(ja, jb + 1):
                        v1 += vr[k]
                    v1 /= (jb - ja + 1)
                    v2 = 0.0
                    for k in range(jb + 1, jc + 1):
                        v2 += vr[k]
                    v2 /= (jc - jb)
                    ok = v2 < v1
                if ok and x_e9 == x_e9 and x_c > x_ph and x_c > x_e9 and x_c <= B - 0.3 * ab:
                    sp = C - 0.03 * a
                    tp = B if tmode == 0 else C + ab
                    if sp < x_c and tp > x_c:
                        m[i] = True
                        stop[i] = sp * sg
                        tgt[i] = tp * sg
            if jc < 0 or lo_i < (l[jc] if sg > 0 else -h[jc]):
                if i - jb >= 1:
                    jc = i
    return m, stop, tgt


def compute(df):
    n = len(df)
    if n == 0:
        return np.zeros(n, bool), np.full(n, np.nan), np.full(n, np.nan)
    f = lambda k: df[k].to_numpy(float)
    c, h, l, atr = f("close"), f("high"), f("low"), f("atr_d")
    with np.errstate(invalid="ignore", divide="ignore"):
        if SIDE == "long":
            ext = c - f("dist_lod_atr") * atr
        else:
            ext = c + f("dist_hod_atr") * atr
        vw = c / (1 + f("vwapDistPct") / 100)
    b, e = _segments(df)
    e9 = _ema9(b, e, c, f("emaDiff"))
    return _kernel(b, e, df["tod"].to_numpy(np.int64), c, h, l, ext, vw, e9, f("volumeRatio"), atr,
                   1.0 if SIDE == "long" else -1.0, 0 if TARGET == "B" else 1, WINDOW[0], WINDOW[1])


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
