"""pod-cwt-unger-maxhigh-afternoon-long - Afternoon break of max(PDH, morning high) on an inside-range open (LONG leg).

Source: Andrea Unger (named Chat With Traders guest list); Unger Academy DAX intraday breakout - long above the higher
of today's and yesterday's high, short below the lower of the lows, flat at the close.
URL: https://ungeracademy.com/blog/systematic-trading-on-dax-trend-following-and-bias-must-know-on-stop-loss-and-take-profit

VARIANT of CWT10 PDH breakout day-two (cwt-a-a3, failed) and the GEN NewHOD specs. Stated changes: the open must be
INSIDE the prior-day range, the level is max(PDH, morning high) fixed at 12:00, afternoon-only window, hold to close.

Rules (plain English, long leg; the short leg is pod-cwt-unger-maxhigh-afternoon-short.py):
  1. Today's open is strictly between the prior-day low and the prior-day high (open = close / (1 + fromOpen/100)).
  2. At the 12:00 bar: L_up = max(PDH, high of day as of the 12:00 bar). The 12:00 values are taken from the last
     frame bar with close time 11:50-12:00, so only completed bars are used.
  3. 12:05-14:30: the first 5-minute close that crosses above L_up (previous close <= L_up), closes above the session
     VWAP, with volumeRatio >= 1.3. Entry at that close.
  Stop (GEOM S): the midpoint of the 09:30-12:00 range, but never more than 0.8 x daily ATR below the entry.
  Exit: flat at 15:55, no target. Costs in (scorer).
No tweaks: every number is the idea's own. Frame note: the running high/low of day come from dist_hod_atr /
dist_lod_atr (they include the 09:30-09:45 bars that the frame does not carry).
Educational only - not financial advice."""
import numba
import numpy as np
import pandas as pd

SIDE = "long"
GEOM = "S"
WINDOW = (1205, 1430)
VR_MIN = 1.3
STOP_CAP_ATR = 0.8
LAYERS = ["open strictly inside the prior-day range", "L_up = max(PDH, HOD at 12:00)",
          "12:05-14:30 first close crossing above L_up", "close above session VWAP", "volumeRatio >= 1.3",
          "stop = 09:30-12:00 midpoint capped at 0.8 ATR, flat 15:55"]

_STASH = {}


def _segments(df):
    k = pd.factorize(pd.Series(df["symbol"].astype(str).to_numpy()) + "|" + pd.Series(df["date"].astype(str).to_numpy()))[0]
    n = len(k)
    if n == 0:
        return np.zeros(0, np.int64), np.zeros(0, np.int64)
    b = np.flatnonzero(np.r_[True, k[1:] != k[:-1]])
    return b.astype(np.int64), np.r_[b[1:], n].astype(np.int64)


@numba.njit(cache=False)
def _kernel(b, e, tod, c, h, l, hod, lod, pdh, pdl, opn, vw, vr, atr, side, vrmin, cap, w0, w1):
    n = len(c)
    m = np.zeros(n, np.bool_)
    stop = np.full(n, np.nan)
    for s in range(len(b)):
        i0, i1 = b[s], e[s]
        h12 = np.nan
        l12 = np.nan
        rh = -1e18
        rl = 1e18
        for i in range(i0, i1):
            rh = max(rh, h[i])
            rl = min(rl, l[i])
            if tod[i] <= 1200 and tod[i] >= 1150:
                h12 = max(hod[i], rh)
                l12 = min(lod[i], rl)
        if not (h12 == h12) or not (l12 == l12):
            continue
        o = opn[i0]
        if not (o > pdl[i0] and o < pdh[i0]):
            continue
        if side == 1:
            lev = max(pdh[i0], h12)
        else:
            lev = min(pdl[i0], l12)
        mid = 0.5 * (h12 + l12)
        for i in range(i0 + 1, i1):
            if tod[i] < w0 or tod[i] > w1:
                continue
            if side == 1:
                ok = c[i] > lev and c[i - 1] <= lev and c[i] > vw[i]
            else:
                ok = c[i] < lev and c[i - 1] >= lev and c[i] < vw[i]
            if ok and vr[i] >= vrmin:
                m[i] = True
                if side == 1:
                    stop[i] = max(mid, c[i] - cap * atr[i])
                else:
                    stop[i] = min(mid, c[i] + cap * atr[i])
    return m, stop


def compute(df, side):
    n = len(df)
    if n == 0:
        return np.zeros(0, bool), np.zeros(0)
    f = lambda k: df[k].to_numpy(float)
    c, h, l, atr = f("close"), f("high"), f("low"), f("atr_d")
    with np.errstate(invalid="ignore", divide="ignore"):
        hod = c + f("dist_hod_atr") * atr
        lod = c - f("dist_lod_atr") * atr
        pdh = c + f("dist_pdh_atr") * atr
        pdl = c - f("dist_pdl_atr") * atr
        opn = c / (1 + f("fromOpen") / 100)
        vw = c / (1 + f("vwapDistPct") / 100)
    b, e = _segments(df)
    return _kernel(b, e, df["tod"].to_numpy(np.int64), c, h, l, hod, lod, pdh, pdl, opn, vw, f("volumeRatio"), atr,
                   1 if side == "long" else -1, VR_MIN, STOP_CAP_ATR, WINDOW[0], WINDOW[1])


def mask(df) -> np.ndarray:
    m, stop = compute(df, SIDE)
    _STASH.clear()
    _STASH[id(df)] = stop
    return m


def stop_price(f, i):
    s = _STASH.get(id(f))
    if s is None or len(s) != len(f):
        mask(f)
        s = _STASH[id(f)]
    return float(s[i])
