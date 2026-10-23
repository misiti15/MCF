"""pod-cwt-breitstein-same-price-ev-gate - New-HOD break only after a below-open dip and reclaim, with a market
tailwind (LONG). Structural stop, hold to 15:55 (the primary). The holdtr exit proxy is
pod-cwt-breitstein-same-price-ev-gate-holdtr.py.

Source: Lance Breitstein, Chat With Traders 236 (same price, different expected value; context decides the EV).
URL: https://chatwithtraders.com/228

VARIANT of R07 HOD break (full day, failed) and CWT46. Stated change: the break counts only if the stock FIRST traded
>= 0.4 ATR below its open after 09:50 and then reclaimed the open and VWAP (right side of a V), plus a market-tailwind
gate. Not CWT12 (no coil) and not heat_fade_long (that buys the dip).

Rules (plain English):
  1. After 09:50 (bars closing 09:55 or later) the bar low traded >= 0.4 x daily ATR below today's open
     (open = close / (1 + fromOpen/100)); after that a 5-minute close back above the open AND above the session VWAP
     (the reclaim bar).
  2. At the entry bar: spy_fo > 0, qqq_fo > 0 and qqq_vwap > 0.
  3. 10:30-14:00, after the reclaim: the first close above the high of day as of the previous bar, with
     volumeRatio >= 1.5. Entry at that close.
  Stop (GEOM S): the lowest low since the reclaim bar (reclaim bar included), never more than 0.8 x daily ATR below
  the entry. No target, flat 15:55 (the idea's EMA9 close trail is not in the harness; holdtr is the separate proxy
  config). Costs in (scorer). No tweaks.
Educational only - not financial advice."""
import numba
import numpy as np
import pandas as pd

SIDE = "long"
GEOM = "S"
WINDOW = (1030, 1400)
CONTEXT = ["spy_fo", "qqq_fo", "qqq_vwap"]
DIP_ATR = 0.4
LAYERS = ["after 09:50 low <= open - 0.4 ATR", "then a close above the open and above VWAP",
          "spy_fo > 0, qqq_fo > 0, qqq_vwap > 0", "10:30-14:00 first close above the prior HOD with volumeRatio >= 1.5",
          "stop lowest low since the reclaim, capped 0.8 ATR, flat 15:55"]

_STASH = {}


def _segments(df):
    k = pd.factorize(pd.Series(df["symbol"].astype(str).to_numpy()) + "|" + pd.Series(df["date"].astype(str).to_numpy()))[0]
    n = len(k)
    if n == 0:
        return np.zeros(0, np.int64), np.zeros(0, np.int64)
    b = np.flatnonzero(np.r_[True, k[1:] != k[:-1]])
    return b.astype(np.int64), np.r_[b[1:], n].astype(np.int64)


@numba.njit(cache=False)
def _kernel(b, e, tod, c, h, l, hod, opn, vw, vr, spy, qqq, qv, atr, dip, w0, w1):
    n = len(c)
    m = np.zeros(n, np.bool_)
    stop = np.full(n, np.nan)
    for s in range(len(b)):
        i0, i1 = b[s], e[s]
        o = opn[i0]
        dipped = False
        rec = False
        mlow = 1e18
        rh = h[i0]
        hprev = max(hod[i0], h[i0])
        for i in range(i0 + 1, i1):
            if not dipped and tod[i] >= 955 and l[i] <= o - dip * atr[i]:
                dipped = True
            elif dipped and not rec and c[i] > o and c[i] > vw[i]:
                rec = True
                mlow = l[i]
            elif rec:
                mlow = min(mlow, l[i])
                if tod[i] >= w0 and tod[i] <= w1 and c[i] > hprev and vr[i] >= 1.5 and spy[i] > 0 and qqq[i] > 0 \
                        and qv[i] > 0:
                    m[i] = True
                    stop[i] = max(mlow, c[i] - 0.8 * atr[i])
            rh = max(rh, h[i])
            hprev = max(hod[i], rh)
    return m, stop


def compute(df):
    n = len(df)
    if n == 0 or not all(k in df for k in CONTEXT):
        return np.zeros(n, bool), np.full(n, np.nan)
    f = lambda k: df[k].to_numpy(float)
    c, h, l, atr = f("close"), f("high"), f("low"), f("atr_d")
    with np.errstate(invalid="ignore", divide="ignore"):
        hod = c + f("dist_hod_atr") * atr
        opn = c / (1 + f("fromOpen") / 100)
        vw = c / (1 + f("vwapDistPct") / 100)
    b, e = _segments(df)
    return _kernel(b, e, df["tod"].to_numpy(np.int64), c, h, l, hod, opn, vw, f("volumeRatio"), f("spy_fo"),
                   f("qqq_fo"), f("qqq_vwap"), atr, DIP_ATR, WINDOW[0], WINDOW[1])


def mask(df) -> np.ndarray:
    m, stop = compute(df)
    _STASH.clear()
    _STASH[id(df)] = stop
    return m


def stop_price(f, i):
    s = _STASH.get(id(f))
    if s is None or len(s) != len(f):
        mask(f)
        s = _STASH[id(f)]
    return float(s[i])
