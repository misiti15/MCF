"""pod-dalton-quiet-poc-revert-long - Quiet balance day: buy a stretch below the developing session POC, target the
POC (LONG).

Source: Axia Futures Volume Profile course / Dalton balance-day behaviour (price rotates back to the developing POC on
balance days) + Jigsaw 'thin markets' trade video. Not re-fetched this round.
URL: https://www.jigsawtrading.com/blog/trade-video-using-order-flow-manage-trades-thin-markets/

VARIANT of 'Reddit R03-vwap-fade: VWAP rubber-band fade' (both sides, failed). Stated change: the anchor is the
developing session POC (volume mode of 5-min typical prices), not VWAP, and only on balance days.
Rules (plain English, 5-minute bars, signal bar close 12:00-14:45):
  1. Balance gate: no new session high or low in the last 60 min (HOD / LOD equal their values 12 bars ago); the IB
     (09:30-10:30, HOD - LOD as of the 10:30 bar) is >= 60% of the session range so far; |spy_fo| <= 0.35%.
  2. The developing POC has stayed within 0.15 x atr_d of its 12:00 value on every bar since 12:00.
  3. The prior bar (the stretch bar) closed >= 0.3 x atr_d below the POC but above the session low, with
     volumeRatio <= 1.0 (drift, not news).
  4. This bar closes above the prior bar's high.
  Entry: that close. Stop (GEOM S): session low - 0.05 x ATR5m, capped at 1.2 x the entry-to-POC distance. Target:
  the POC (as of the entry bar).
Harness approximations (pre-declared): there is no raw volume column, so the POC is the mode of typical price
(H+L+C)/3 weighted by volumeRatio (bar volume / its 20-bar average, close to proportional to volume within a day),
in bins of 0.02 x atr_d, built from the 09:50 bar on (the 09:30-09:45 bars are not in the frames); ties keep the
earlier POC. The source window opens 11:30, but rule 2 needs the 12:00 POC, so signals start 12:00. The source's
15:30 time stop is not expressible (the scorer flattens at 15:55). No tweak used. No tuning on valid.
Costs per config/default.yaml (applied by the scorer). Only bars up to the decision bar are used.
Educational only - not financial advice."""
SIDE = "long"
GEOM = "S"
WINDOW = (1200, 1445)
CONTEXT = ["spy_fo"]
LAYERS = ["no new HOD/LOD in 60 min, IB >= 60% of day range, |spy_fo| <= 0.35",
          "POC within 0.15 ATR of its 12:00 value since 12:00",
          "prior close >= 0.3 ATR below POC, above LOD, volumeRatio <= 1.0", "close > prior bar high",
          "stop LOD - 0.05 ATR5m capped 1.2x POC distance, target POC"]

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


NB = 1001


@numba.njit(cache=False)
def _poc(st, tod, h, l, c, atr, vr):
    """Developing POC per row (volumeRatio-weighted typical-price mode, bins of 0.02 x atr_d), and the max deviation
    of the POC from its 12:00 value since 12:00 (NaN before 12:00)."""
    n = len(c)
    poc = np.full(n, np.nan)
    dev = np.full(n, np.nan)
    hist = np.zeros(NB)
    base = 0.0
    w = 0.0
    best = -1
    bw = 0.0
    p12 = np.nan
    dmax = 0.0
    for i in range(n):
        if st[i]:
            hist[:] = 0.0
            tp0 = (h[i] + l[i] + c[i]) / 3.0
            base = tp0
            w = 0.02 * atr[i]
            best = -1
            bw = 0.0
            p12 = np.nan
            dmax = 0.0
        if not (w > 0):
            continue
        tp = (h[i] + l[i] + c[i]) / 3.0
        v = vr[i]
        if np.isfinite(tp) and np.isfinite(v) and v > 0:
            b = int(np.floor((tp - base) / w + 0.5)) + NB // 2
            if b < 0:
                b = 0
            if b >= NB:
                b = NB - 1
            hist[b] += v
            if hist[b] > bw:
                bw = hist[b]
                best = b
        if best >= 0:
            poc[i] = base + (best - NB // 2) * w
        if tod[i] == 1200:
            p12 = poc[i]
            dmax = 0.0
        if tod[i] >= 1200 and np.isfinite(p12):
            d = abs(poc[i] - p12)
            if d > dmax:
                dmax = d
            dev[i] = dmax
    return poc, dev


def _lag(x, k, n=1):
    x = np.asarray(x, float)
    p = np.full(len(x), np.nan)
    if len(x) > n:
        p[n:] = x[:-n]
        p[n:][k[n:] != k[:-n]] = np.nan
    return p


def _at(x, k, tod, T):
    gv = np.full(int(k.max()) + 1 if len(k) else 1, np.nan)
    sel = tod == T
    gv[k[sel]] = np.asarray(x, float)[sel]
    return gv[k]


def mask(df) -> np.ndarray:
    _ST.clear()
    z = np.zeros(len(df), dtype=bool)
    if not len(df) or "spy_fo" not in df:
        return z
    k = _key(df)
    tod = df["tod"].to_numpy(np.int64)
    c, h, l, atr = _f(df, "close"), _f(df, "high"), _f(df, "low"), _f(df, "atr_d")
    vr = _f(df, "volumeRatio")
    with np.errstate(invalid="ignore", divide="ignore"):
        hod = c + _f(df, "dist_hod_atr") * atr
        lod = c - _f(df, "dist_lod_atr") * atr
        atr5 = _f(df, "atrPct") * c / 100
        poc, dev = _poc(_start(k), tod, h, l, c, atr, vr)
        tol = 1e-6 * c
        m = (np.abs(hod - _lag(hod, k, 12)) <= tol) & (np.abs(lod - _lag(lod, k, 12)) <= tol)
        ib = _at(hod - lod, k, tod, 1030)
        m &= ib >= 0.6 * (hod - lod)
        m &= np.abs(_f(df, "spy_fo")) <= 0.35
        m &= dev <= 0.15 * atr
        pc, plod, pvr, ppoc = _lag(c, k), _lag(lod, k), _lag(vr, k), _lag(poc, k)
        m &= (pc <= ppoc - 0.3 * atr) & (pc > plod) & (pvr <= 1.0)
        m &= c > _lag(h, k)
        m &= (tod >= WINDOW[0]) & (tod <= WINDOW[1])
        dist = poc - c
        m &= dist > 0
        stop = np.maximum(lod - 0.05 * atr5, c - 1.2 * dist)
        m &= stop < c
    _ST[id(df)] = (stop, poc)
    return np.asarray(m & np.isfinite(stop) & np.isfinite(poc), dtype=bool)
