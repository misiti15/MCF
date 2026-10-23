"""pod-cwt2-cortes-elephant-bar-gift-zone-long - Elephant bar at a daily support: buy the 50% retrace into its body
(LONG).

Source: Chat With Traders ep 309, Diego Ivan Cortes Lopez; record ep309 'Elephant bar gift zone re-entry'.
URL: https://chatwithtraders.com

VARIANT of pod-of-defended-origin-retest (a FULL retrace to a high-VOLUME impulse bar's low on light volume, in an
uptrend above VWAP). Stated change: the impulse is a RANGE-defined reversal bar (elephant) printed AFTER a decline AT
a daily support level, and the entry is at 50% of that bar (the 'gift zone'), not at its origin.

Rules (plain English), bars up to the decision bar only:
  1. Decline: before bar E, price fell >= 0.6 x atr_d from today's open or the high of day: max(open, HOD as of
     bar E-1) - low(E) >= 0.6 x atr_d.
  2. Location: E's low is within 0.15 x atr_d of the prior-day low, the prior-day close (open / (1 + gap)), or a
     round number (step $5 >= $100, $1 >= $20, else $0.5; measured from E's low), or E's low is the running LOD.
  3. Elephant bar E (bar close 09:50-11:00): range >= 2.5 x the mean range of the prior 10 bars, close in the top
     25% of its range, close > the prior close (proxy for close > open: the frame has no open column).
     Proxy (stated): the frame starts at 09:50, so for E bars with fewer than 10 earlier frame bars the 5-minute
     ATR(14) at bar E-1 (atrPct x close) stands in for the 10-bar mean range.
  4. Within the next 6 bars, a bar's low touches E_mid = (E high + E low)/2, while no close from E+1 up to and
     including that bar is below E low + 0.2 x E range (no > 80% retrace). Only the first touch counts; the trade is
     taken if that touching bar closes >= E_mid (the frame's close-entry rule for the E_mid limit).
  Entry: the touching bar's close, bar close 09:55-11:30. Stop (GEOM S): E low - 0.05 x atr_d. Target: 2R. Flat 15:55.
  Costs in (scorer). No tweak used (all thresholds as written in the idea).
Educational only - not financial advice."""
import numba
import numpy as np
import pandas as pd

SIDE = "long"
GEOM = "S"
WINDOW = (955, 1130)
CONTEXT = []
LAYERS = ["decline >= 0.6 ATR from open / HOD into E", "E low within 0.15 ATR of PDL / prior close / round, or LOD",
          "E (09:50-11:00): range >= 2.5 x 10-bar mean, close top 25%, close > prior close",
          "within 6 bars: low touches E mid, no close below E low + 0.2 range, touching bar closes >= E mid",
          "stop E low - 0.05 ATR, target 2R", "09:55-11:30 ET"]

_STASH = {}


def _segments(df):
    k = pd.factorize(pd.Series(df["symbol"].astype(str).to_numpy()) + "|" + pd.Series(df["date"].astype(str).to_numpy()))[0]
    n = len(k)
    if n == 0:
        return np.zeros(0, np.int64), np.zeros(0, np.int64)
    b = np.flatnonzero(np.r_[True, k[1:] != k[:-1]])
    return b.astype(np.int64), np.r_[b[1:], n].astype(np.int64)


@numba.njit(cache=False)
def _kernel(b, e, tod, c, h, l, op, hod, lod, pdl, pc, atr, atr5, w0, w1):
    n = len(c)
    m = np.zeros(n, np.bool_)
    stop = np.full(n, np.nan)
    tgt = np.full(n, np.nan)
    for s in range(len(b)):
        i0, i1 = b[s], e[s]
        done = False
        for E in range(i0 + 1, i1):
            if done:
                break
            if tod[E] < 950 or tod[E] > 1100:
                continue
            a = atr[E]
            if not (a > 0):
                continue
            rg = h[E] - l[E]
            if not (rg > 0):
                continue
            if E - i0 >= 10:
                mr = 0.0
                for k in range(E - 10, E):
                    mr += h[k] - l[k]
                mr /= 10.0
            else:
                mr = atr5[E - 1]
            if not (mr > 0 and rg >= 2.5 * mr):
                continue
            if not ((c[E] - l[E]) >= 0.75 * rg and c[E] > c[E - 1]):
                continue
            ref = max(op[E], hod[E - 1])
            if not (ref - l[E] >= 0.6 * a):
                continue
            px = l[E]
            step = 5.0 if px >= 100 else (1.0 if px >= 20 else 0.5)
            rd = abs(px - np.round(px / step) * step) / a
            loc = (abs(px - pdl[E]) <= 0.15 * a) or (abs(px - pc[E]) <= 0.15 * a) or (rd <= 0.15) \
                or (px <= lod[E] + 1e-9 * px)
            if not loc:
                continue
            mid = 0.5 * (h[E] + l[E])
            floor = l[E] + 0.2 * rg
            for j in range(E + 1, min(i1, E + 7)):
                if c[j] < floor:
                    break
                if l[j] <= mid:
                    if c[j] >= mid and tod[j] >= w0 and tod[j] <= w1:
                        sp = l[E] - 0.05 * a
                        if sp < c[j]:
                            m[j] = True
                            stop[j] = sp
                            tgt[j] = c[j] + 2.0 * (c[j] - sp)
                            done = True
                    break
    return m, stop, tgt


def compute(df):
    n = len(df)
    if n == 0:
        return np.zeros(n, bool), np.full(n, np.nan), np.full(n, np.nan)
    f = lambda k: df[k].to_numpy(float)
    c, atr = f("close"), f("atr_d")
    with np.errstate(invalid="ignore", divide="ignore"):
        op = c / (1 + f("fromOpen") / 100)
        pc = op / (1 + f("gap") / 100)
        hod = c + f("dist_hod_atr") * atr
        lod = c - f("dist_lod_atr") * atr
        pdl = c - f("dist_pdl_atr") * atr
        atr5 = f("atrPct") * c / 100
    b, e = _segments(df)
    return _kernel(b, e, df["tod"].to_numpy(np.int64), c, f("high"), f("low"), op, hod, lod, pdl, pc, atr, atr5,
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
