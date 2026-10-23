"""pod-bbt-orb-vwap-pullback-atr-room-long - Post-opening-range-break first pullback to VWAP with ATR room left (LONG).

Source: Bear Bull Traders '5 Min ORB Strategy' deck (Apr 2023) and BBT TradeBook Breakouts (2025): wait for pullbacks
near VWAP; target 80-100% of ATR.
URL: https://bearbulltraders.com/wp-content/uploads/2023/04/5-Min-ORB-Strategy-ORB.pdf

VARIANT of vwap_pullback (in-play VWAP pullback, 1.5R target), orb20_a / R01 ORB30 and bdi-tg-p-pullback-vwap-long
(failed: non-selective). Stated changes: a completed OR break must come first, an unused-ATR-room gate, and an ATR-room
target.

Opening range: 09:30-09:50 (the harness frame starts at the 09:50 bar; the source uses 5-15 min). OR high / low = the
high / low of day as of the 09:50 bar close (dist_hod_atr / dist_lod_atr on that row), so it is known from 09:50 on.
EMA9: the true continuous 5-minute EMA9 recovered exactly from emaDiff (EMA9 = EMA21 x (1 + emaDiff); seeds solved
from the 09:50 and 09:55 rows), known from 09:55.

Rules (plain English), decision bar i:
  1. |gap| >= 2% or rvol >= 2, rvol = mean volumeRatio of today's bars 09:50..i (the frame has no raw volume; proxy).
  2. An earlier bar today (09:55..i-1) closed above the OR high.
  3. low_i <= VWAP_i + 0.05 x daily ATR (touched VWAP), close_i > VWAP_i and close_i > OR low.
  4. Today's range so far (HOD - LOD) <= 0.6 x daily ATR (ATR room left).
  5. EMA9_i >= VWAP_i.
  Entry: the first qualifying close, 10:00-11:30. Stop (GEOM S): min(VWAP - 0.1 x daily ATR, low_i).
  Target: LOD + 0.9 x daily ATR (source 80-100%; pre-declared middle 0.9); skip if it is not above the entry.
  Flat 15:55. Costs in (scorer). No tweak used.
Educational only - not financial advice."""
import numba
import numpy as np
import pandas as pd

SIDE = "long"
GEOM = "S"
WINDOW = (1000, 1130)
CONTEXT = []
LAYERS = ["|gap| >= 2% or mean volumeRatio since 09:50 >= 2", "earlier close above the 09:30-09:50 high",
          "low touches VWAP + 0.05 ATR, close > VWAP and > OR low", "day range <= 0.6 ATR", "EMA9 >= VWAP",
          "stop min(VWAP - 0.1 ATR, bar low), target LOD + 0.9 ATR", "10:00-11:30 ET"]

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
def _kernel(b, e, tod, c, h, l, hod, lod, vw, e9, gap, vr, atr, w0, w1):
    n = len(c)
    m = np.zeros(n, np.bool_)
    stop = np.full(n, np.nan)
    tgt = np.full(n, np.nan)
    for s in range(len(b)):
        i0, i1 = b[s], e[s]
        if tod[i0] != 950:
            continue
        orh, orl = hod[i0], lod[i0]
        broke = False
        rv = 0.0
        for i in range(i0, i1):
            rv += vr[i]
            if i > i0 and tod[i] >= w0 and tod[i] <= w1 and broke:
                a = atr[i]
                rvol = rv / (i - i0 + 1)
                if (abs(gap[i]) >= 2.0 or rvol >= 2.0) and l[i] <= vw[i] + 0.05 * a and c[i] > vw[i] \
                        and c[i] > orl and hod[i] - lod[i] <= 0.6 * a and e9[i] == e9[i] and e9[i] >= vw[i]:
                    sp = min(vw[i] - 0.1 * a, l[i])
                    tp = lod[i] + 0.9 * a
                    if sp < c[i] and tp > c[i]:
                        m[i] = True
                        stop[i] = sp
                        tgt[i] = tp
            if i > i0 and c[i] > orh:
                broke = True
    return m, stop, tgt


def compute(df):
    n = len(df)
    if n == 0:
        return np.zeros(n, bool), np.full(n, np.nan), np.full(n, np.nan)
    f = lambda k: df[k].to_numpy(float)
    c, h, l, atr = f("close"), f("high"), f("low"), f("atr_d")
    with np.errstate(invalid="ignore", divide="ignore"):
        hod = c + f("dist_hod_atr") * atr
        lod = c - f("dist_lod_atr") * atr
        vw = c / (1 + f("vwapDistPct") / 100)
    b, e = _segments(df)
    e9 = _ema9(b, e, c, f("emaDiff"))
    return _kernel(b, e, df["tod"].to_numpy(np.int64), c, h, l, hod, lod, vw, e9, f("gap"), f("volumeRatio"), atr,
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
