"""pod-shannon-pdh-vwap-confluence-retest-long - PDH and VWAP converge as support: buy the first retest from above
(LONG).

Source: Brian Shannon / Alpha Trends - multiple-timeframe level confluence (a higher-timeframe level plus VWAP/AVWAP as
shared support for buyers). Not re-fetched in round 2.
URL: https://alphatrends.net

VARIANT of pod-of-pdh-time-acceptance-long (time accepted above the PDH) and CWT10 PDH breakout. Stated change: the
PDH must coincide with VWAP, and entry is on the light-volume retest of that shared level, not on the break.

Definitions: PDH = close + dist_pdh_atr x atr_d (prior completed day's high); VWAP = close / (1 + vwapDistPct/100);
L = max(PDH, VWAP); lo = min(PDH, VWAP).
Rules (plain English), only bars up to and including the decision bar i of the same symbol-day:
  1. At least one earlier close above the PDH on a bar closing 10:15 or later today.
  2. |VWAP - PDH| <= 0.15 x daily ATR at the trigger bar.
  3. Trigger bar: low <= L + 0.05 ATR, close >= L + 0.03 ATR, lower_wick >= 0.35, volumeRatio <= 1.2.
  4. No close below lo - 0.10 ATR (each bar's own VWAP) from the first PDH-break bar through i.
  5. breadth >= 0.45.
  Entry: trigger close, bar close 10:30-14:30 (first qualifying retest per symbol-day). Stop (GEOM S): lo - 0.10 x
  daily ATR. Target: the nearer of the high of day (at entry) and entry + 2R; skip when the HOD is not above entry.
  Flat 15:55. Costs in (scorer).
No tweak made.
Educational only - not financial advice."""
import numba
import numpy as np
import pandas as pd

SIDE = "long"
GEOM = "S"
WINDOW = (1030, 1430)
CONTEXT = ["breadth"]
LAYERS = ["a close above PDH after 10:15", "|VWAP - PDH| <= 0.15 ATR", "test of max(PDH,VWAP): low <= L+0.05ATR, close >= L+0.03ATR",
          "lower_wick >= 0.35, volumeRatio <= 1.2", "no close below min(PDH,VWAP)-0.10ATR since the break",
          "breadth >= 0.45", "stop min(PDH,VWAP) - 0.10 ATR, target min(HOD, 2R)", "10:30-14:30 ET"]


@numba.njit(cache=False)
def _kernel(b, e, tod, c, l, pdh, vw, hod, lw, vr, br, atr, w0, w1):
    n = len(c)
    m = np.zeros(n, np.bool_)
    stop = np.full(n, np.nan)
    tgt = np.full(n, np.nan)
    for s in range(len(b)):
        i0, i1 = b[s], e[s]
        broke = False      # a close above PDH at 10:15+ on an EARLIER bar
        broke_now = False
        failed = False
        for i in range(i0, i1):
            a = atr[i]
            if not (pdh[i] == pdh[i]):
                continue
            broke = broke_now
            if broke and c[i] < min(pdh[i], vw[i]) - 0.10 * a:
                failed = True
            if not broke_now and tod[i] >= 1015 and c[i] > pdh[i]:
                broke_now = True
            if failed:
                break
            if not broke or tod[i] < w0 or tod[i] > w1:
                continue
            if not (abs(vw[i] - pdh[i]) <= 0.15 * a and br[i] >= 0.45):
                continue
            L = max(pdh[i], vw[i])
            if not (l[i] <= L + 0.05 * a and c[i] >= L + 0.03 * a and lw[i] >= 0.35 and vr[i] <= 1.2):
                continue
            sp = min(pdh[i], vw[i]) - 0.10 * a
            R = c[i] - sp
            if not (R > 0 and hod[i] > c[i]):
                continue
            m[i] = True
            stop[i] = sp
            tgt[i] = min(hod[i], c[i] + 2.0 * R)
    return m, stop, tgt


def compute(df):
    n = len(df)
    if n == 0 or "breadth" not in df:
        return np.zeros(n, bool), np.full(n, np.nan), np.full(n, np.nan)
    f = lambda k: df[k].to_numpy(float)
    c, atr = f("close"), f("atr_d")
    with np.errstate(invalid="ignore", divide="ignore"):
        pdh = c + f("dist_pdh_atr") * atr
        vw = c / (1 + f("vwapDistPct") / 100)
        hod = c + f("dist_hod_atr") * atr
    b, e = _segments(df)
    return _kernel(b, e, df["tod"].to_numpy(np.int64), c, f("low"), pdh, vw, hod, f("lower_wick"), f("volumeRatio"),
                   f("breadth"), atr, WINDOW[0], WINDOW[1])


_STASH = {}


def _segments(df):
    k = pd.factorize(pd.Series(df["symbol"].astype(str).to_numpy()) + "|" + pd.Series(df["date"].astype(str).to_numpy()))[0]
    n = len(k)
    if n == 0:
        return np.zeros(0, np.int64), np.zeros(0, np.int64)
    b = np.flatnonzero(np.r_[True, k[1:] != k[:-1]])
    return b.astype(np.int64), np.r_[b[1:], n].astype(np.int64)


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
