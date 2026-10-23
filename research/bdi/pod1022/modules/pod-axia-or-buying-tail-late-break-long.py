"""pod-axia-or-buying-tail-late-break-long - Opening-range buying tail (excess at the OR30 low), then a late break of
the OR30 high on a quiet day (LONG).

Source: Axia Futures / Market Profile 'excess' (a single-print buying tail ends the down auction) + Dalton open types.
Not re-fetched this round.
URL: https://nexusfi.com/articles/trading/Opening-Types

VARIANT of orb20_a / t2-orb15 (plain opening-range breaks) and wi-ib-narrow-extension. Stated change: the OR30 low
must be an EXCESS tail (one bar, long lower wick, above-average volume), and the break is traded only late
(11:00-14:30) after the range has held, on a narrow-to-normal range.
Rules (plain English, 5-minute bars):
  OR30 = 09:30-10:00; ORH / ORL = the high / low of day as of the 10:00 bar (dist_hod_atr / dist_lod_atr), mid = avg.
  1. Excess: the ORL was made by one 5-min bar with lower wick >= 50% of its range and volumeRatio >= 1.5, and no
     other OR bar's low is within 0.1 x ATR5m of it.
  2. From 10:05 to the signal, no 5-min close below the OR30 midpoint.
  3. The signal bar is the first close above the ORH after 10:00, bar close 11:00-14:30, volumeRatio >= 1.2.
  4. OR30 range <= 0.6 x atr_d.
  Entry: signal close. Stop (GEOM S): OR30 midpoint. Target: ORH + 1 x OR30 range (else flat 15:55).
Harness approximations (pre-declared): frames start at the 09:50 bar, so the tail bar must be one of the visible OR
bars (09:45-09:50, 09:50-09:55, 09:55-10:00); days whose ORL was printed 09:30-09:45 are skipped (not observable).
When the tail is the 09:50 bar, the 09:30-09:45 lows can only be bounded by it being the low of day (the 0.1 x ATR5m
separation is checked against the visible bars and, for the 09:55 / 10:00 tails, against the low of day before
them). There is no raw volume: 'volume >= 1.5x the OR-bar average' is read as volumeRatio >= 1.5 (bar / 20-bar
average) and '1.2x the 20-bar average' as volumeRatio >= 1.2. The source's 'or hold to 15:55 / holdtr' alternative
is not used (one geometry, the stated target). No tweak used. No tuning on valid.
Costs per config/default.yaml (applied by the scorer). Only bars up to the decision bar are used.
Educational only - not financial advice."""
SIDE = "long"
GEOM = "S"
WINDOW = (1100, 1430)
CONTEXT = []
LAYERS = ["OR30 low = single visible bar, lower wick >= 0.5, volumeRatio >= 1.5, no other OR low within 0.1 ATR5m",
          "no close below the OR30 mid since 10:05", "first close above ORH, 11:00-14:30, volumeRatio >= 1.2",
          "OR30 range <= 0.6 ATR", "stop OR mid, target ORH + OR range"]

import sys
from pathlib import Path

import numba
import numpy as np
import pandas as pd

_ST = {}
_DC = {}


def _f(df, c):
    return df[c].to_numpy(float) if c in df else np.full(len(df), np.nan)


def _key(df):
    """Symbol-day group code (frames are sorted by symbol, date, tod, so groups are contiguous)."""
    s = pd.Series(df["symbol"].astype(str).to_numpy()) + "|" + pd.Series(df["date"].astype(str).to_numpy())
    return pd.factorize(s)[0]


def _start(k):
    return np.r_[True, k[1:] != k[:-1]] if len(k) else np.zeros(0, bool)


def _stash_get(f, i, j):
    s = _ST.get(id(f))
    if s is None or len(s[0]) != len(f):
        mask(f)
        s = _ST.get(id(f))
    return float(s[j][i]) if s is not None else float("nan")


def stop_price(f, i):
    return _stash_get(f, i, 0)


def target_price(f, i, stop):
    return _stash_get(f, i, 1)


@numba.njit(cache=False)
def _scan(st, tod, h, l, c, hod, lod, atr, atr5, lw, vr):
    n = len(c)
    m = np.zeros(n, np.bool_)
    stop = np.full(n, np.nan)
    tgt = np.full(n, np.nan)
    i = 0
    while i < n:
        e = i + 1
        while e < n and not st[e]:
            e += 1
        # day = rows i..e-1
        r950 = -1
        r955 = -1
        r1000 = -1
        for t in range(i, e):
            if tod[t] == 950:
                r950 = t
            elif tod[t] == 955:
                r955 = t
            elif tod[t] == 1000:
                r1000 = t
        if r950 >= 0 and r955 == r950 + 1 and r1000 == r955 + 1:
            orh = hod[r1000]
            orl = lod[r1000]
            rng = orh - orl
            mid = 0.5 * (orh + orl)
            ok = rng > 0 and rng <= 0.6 * atr[r1000]
            tb = -1
            if ok:
                tol = 1e-6 * c[r1000] + 1e-9
                for t in (r950, r955, r1000):
                    if abs(l[t] - orl) <= tol:
                        tb = t
                        break
            if tb >= 0:
                a5 = atr5[tb]
                sep = 0.1 * a5
                good = lw[tb] >= 0.5 and vr[tb] >= 1.5 and a5 > 0
                for t in (r950, r955, r1000):
                    if t != tb and l[t] <= orl + sep:
                        good = False
                if tb > r950 and lod[tb - 1] <= orl + sep:     # includes the 09:30-09:45 bars
                    good = False
                if good:
                    for t in range(r1000 + 1, e):
                        if c[t] < mid:
                            break
                        if c[t] > orh:
                            if tod[t] >= 1100 and tod[t] <= 1430 and vr[t] >= 1.2:
                                m[t] = True
                                stop[t] = mid
                                tgt[t] = orh + rng
                            break
        i = e
    return m, stop, tgt


def mask(df) -> np.ndarray:
    _ST.clear()
    z = np.zeros(len(df), dtype=bool)
    if not len(df):
        return z
    k = _key(df)
    tod = df["tod"].to_numpy(np.int64)
    c, atr = _f(df, "close"), _f(df, "atr_d")
    with np.errstate(invalid="ignore", divide="ignore"):
        hod = c + _f(df, "dist_hod_atr") * atr
        lod = c - _f(df, "dist_lod_atr") * atr
        atr5 = _f(df, "atrPct") * c / 100
        m, stop, tgt = _scan(_start(k), tod, _f(df, "high"), _f(df, "low"), c, hod, lod, atr, atr5,
                             _f(df, "lower_wick"), _f(df, "volumeRatio"))
        m &= (tod >= WINDOW[0]) & (tod <= WINDOW[1])
    _ST[id(df)] = (stop, tgt)
    return np.asarray(m & np.isfinite(stop) & np.isfinite(tgt), dtype=bool)
