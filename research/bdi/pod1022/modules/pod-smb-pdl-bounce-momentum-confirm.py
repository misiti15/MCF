"""pod-smb-pdl-bounce-momentum-confirm - PDL holds after a selling-exhaustion leg, buy the upside-momentum
confirmation (LONG).

Source: SMB Training blog 'Finding The Bounce - $SPY' (Steven Spencer).
URL: https://www.smbtraining.com/blog/finding-the-bounce-spy

VARIANT of CWT14 failed-PDL-break long (Primary/Testing: needs a break and reclaim) and obos-levels. Stated change: the
level must HOLD (no close below PDL) and entry needs an exhaustion sequence then positive momentum.

No tweak used; values are the source's. Leg definition fixed before scoring: the highest high of bars i-8..i-2 minus
the lowest low of bars i-1..i (the test of the PDL). PDL = close - dist_pdl_atr x atr_d (a completed-day value).

Rules (plain English), decision bar i:
  1. Level: the low of bar i or bar i-1 is 0-0.12 x daily ATR above the prior-day low; no 5-minute close today (from
     09:50 up to bar i) below the PDL.
  2. Exhaustion: >= 3 of bars i-4..i-1 closed below their previous close; the leg >= 0.5 x daily ATR; one of bars
     i-4..i-1 has volumeRatio >= 1.8.
  3. Confirmation: momentum_i > 0 and close_i > max(high_{i-1}, high_{i-2}).
  4. gap > -2%; breadth >= 0.25.
  Entry: close_i, bar close 10:00-14:00, one per symbol-day. Stop (GEOM S): PDL - 0.08 x daily ATR. Target: VWAP or
  entry + 1.5R, whichever is nearer (1.5R when VWAP is not above the entry). Flat 15:55. Costs in (scorer).
Educational only - not financial advice."""
import numba
import numpy as np
import pandas as pd

SIDE = "long"
GEOM = "S"
WINDOW = (1000, 1400)
CONTEXT = ["breadth"]
LAYERS = ["low of bar i or i-1 within 0-0.12 ATR above PDL, no close below PDL today",
          ">= 3 of last 4 bars down, leg >= 0.5 ATR, a volumeRatio >= 1.8 bar",
          "momentum > 0, close > max(high[i-1], high[i-2])", "gap > -2%, breadth >= 0.25",
          "stop PDL - 0.08 ATR, target nearer of VWAP / 1.5R", "10:00-14:00 ET"]

_STASH = {}


def _segments(df):
    k = pd.factorize(pd.Series(df["symbol"].astype(str).to_numpy()) + "|" + pd.Series(df["date"].astype(str).to_numpy()))[0]
    n = len(k)
    if n == 0:
        return np.zeros(0, np.int64), np.zeros(0, np.int64)
    b = np.flatnonzero(np.r_[True, k[1:] != k[:-1]])
    return b.astype(np.int64), np.r_[b[1:], n].astype(np.int64)


@numba.njit(cache=False)
def _kernel(b, e, tod, c, h, l, dpdl, vd, vr, mom, gp, br, atr, w0, w1):
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
            if not (a > 0 and gp[i] > -2.0 and br[i] >= 0.25 and mom[i] > 0 and c[i] > max(h[i - 1], h[i - 2])):
                continue
            pdl = c[i] - dpdl[i] * a
            z0 = (l[i] - pdl) / a
            z1 = (l[i - 1] - pdl) / a
            if not ((z0 >= 0 and z0 <= 0.12) or (z1 >= 0 and z1 <= 0.12)):
                continue
            bad = False
            for k in range(i0, i + 1):
                if c[k] < pdl:
                    bad = True
                    break
            if bad:
                continue
            dn = 0
            clim = False
            for k in range(i - 4, i):
                if c[k] < c[k - 1]:
                    dn += 1
                if vr[k] >= 1.8:
                    clim = True
            if dn < 3 or not clim:
                continue
            hh = -1e18
            for k in range(i - 8, i - 1):
                hh = max(hh, h[k])
            if not (hh - min(l[i - 1], l[i]) >= 0.5 * a):
                continue
            sp = pdl - 0.08 * a
            if not (sp < c[i]):
                continue
            t15 = c[i] + 1.5 * (c[i] - sp)
            vw = c[i] / (1.0 + vd[i] / 100.0)
            tp = min(vw, t15) if vw > c[i] else t15
            m[i] = True
            stop[i] = sp
            tgt[i] = tp
    return m, stop, tgt


def compute(df):
    n = len(df)
    if n == 0 or "breadth" not in df:
        return np.zeros(n, bool), np.full(n, np.nan), np.full(n, np.nan)
    f = lambda k: df[k].to_numpy(float)
    b, e = _segments(df)
    return _kernel(b, e, df["tod"].to_numpy(np.int64), f("close"), f("high"), f("low"), f("dist_pdl_atr"),
                   f("vwapDistPct"), f("volumeRatio"), f("momentum"), f("gap"), f("breadth"), f("atr_d"),
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
