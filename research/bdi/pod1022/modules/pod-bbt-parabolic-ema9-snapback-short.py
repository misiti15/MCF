"""pod-bbt-parabolic-ema9-snapback-short - Parabolic run of large green bars: short the first new 5-min low, target the
5-min EMA9 (SHORT).

Source: Bear Bull Traders - 'How to Trade Parabolic Reversals' (Strategy 3 deck 2023; webinar 25 Mar 2025).
URL: https://bearbulltraders.com/wp-content/uploads/2023/05/how-to-trade-parabolic-reversals-1.pdf

VARIANT of CWT13 VWAP-stretch fade (cwt-b-b2, failed) and VT volume top (videos, failed). Stated changes: stretch
measured from EMA9, >= 3 large green bars + a 2x climax bar, a new-low trigger, EMA9 target.

EMA9: the true continuous 5-minute EMA9 (the one behind the frame's `emaDiff`, carried over many sessions) is recovered
exactly from the frame: EMA9 = EMA21 x (1 + emaDiff/100), and both EMAs follow their recursions over the day's rows, so
the two unknown seeds are solved from the 09:50 and 09:55 rows (checked: reproduces emaDiff to ~1e-6 % on later bars).
It is therefore known from the 09:55 bar on; nothing after bar i is used.

Rules (plain English), decision bar i:
  1. Bars i-3, i-2, i-1 each close above the previous close, each with a range (high - low) >= 0.15 x daily ATR
     (the frame has no open, so "green" = close above the prior close).
  2. high_{i-1} >= 1.02 x EMA9_{i-1} (stretched >= 2% above the 5-minute EMA9).
  3. volumeRatio of bar i-1 or bar i-2 >= 2.0 (climax bar).
  4. No support level between entry and EMA9. The daily SMA50/SMA200 and the 5-minute SMA200 are not in the frame;
     the 5-minute SMA50 (from sma50_dist_pct) stands in for them (stated substitution): it must not lie strictly
     between EMA9_i and close_i.
  5. close_i < low_{i-1} (first new 5-minute low).
  Entry: close_i, 09:50-14:30 bar close. Stop (GEOM S): max high of bars i-3..i + 0.02 x daily ATR.
  Target: EMA9_i at entry; skip if (entry - target) < 1.5 x (stop - entry). Flat 15:55. Costs in (scorer).
  No tweak used.
Educational only - not financial advice."""
import numba
import numpy as np
import pandas as pd

SIDE = "short"
GEOM = "S"
WINDOW = (950, 1430)
CONTEXT = []
LAYERS = ["3 rising closes with range >= 0.15 ATR each", "high_{i-1} >= 1.02 x EMA9", "volumeRatio >= 2 on i-1 or i-2",
          "5m SMA50 not between entry and EMA9", "close < prior bar low",
          "stop max high(i-3..i) + 0.02 ATR, target EMA9, skip if < 1.5R", "09:50-14:30 ET"]

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
def _kernel(b, e, tod, c, h, l, e9, vr, sma50, atr, w0, w1):
    n = len(c)
    m = np.zeros(n, np.bool_)
    stop = np.full(n, np.nan)
    tgt = np.full(n, np.nan)
    for s in range(len(b)):
        i0, i1 = b[s], e[s]
        for i in range(i0 + 4, i1):
            if tod[i] < w0 or tod[i] > w1:
                continue
            a = atr[i]
            ok = True
            for k in range(i - 3, i):
                if not (c[k] > c[k - 1] and h[k] - l[k] >= 0.15 * a):
                    ok = False
                    break
            if not ok:
                continue
            if not (e9[i - 1] == e9[i - 1] and h[i - 1] >= 1.02 * e9[i - 1]):
                continue
            if not (vr[i - 1] >= 2.0 or vr[i - 2] >= 2.0):
                continue
            if not (c[i] < l[i - 1]):
                continue
            t = e9[i]
            if not (t == t and t < c[i]):
                continue
            sm = sma50[i]
            if sm == sm and sm > t and sm < c[i]:
                continue
            hh = max(max(h[i - 3], h[i - 2]), max(h[i - 1], h[i]))
            sp = hh + 0.02 * a
            if not (sp > c[i]):
                continue
            if (c[i] - t) < 1.5 * (sp - c[i]):
                continue
            m[i] = True
            stop[i] = sp
            tgt[i] = t
    return m, stop, tgt


def compute(df):
    n = len(df)
    if n == 0:
        return np.zeros(n, bool), np.full(n, np.nan), np.full(n, np.nan)
    f = lambda k: df[k].to_numpy(float)
    c, h, l, atr = f("close"), f("high"), f("low"), f("atr_d")
    with np.errstate(invalid="ignore", divide="ignore"):
        sma50 = c / (1 + f("sma50_dist_pct") / 100)
    b, e = _segments(df)
    e9 = _ema9(b, e, c, f("emaDiff"))
    return _kernel(b, e, df["tod"].to_numpy(np.int64), c, h, l, e9, f("volumeRatio"), sma50, atr, WINDOW[0], WINDOW[1])


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
