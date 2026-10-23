"""pod-camarilla-l3-quiet-fade-long - Camarilla L3 fade on days that open inside the L3-H3 band (LONG).

Source: Camarilla equation (Nick Scott); LuxAlgo concept library 'Camarilla'; MQL5 'Camarilla trading and pivots'.
URL: https://www.luxalgo.com/library/concept/camarilla/

VARIANT of the classic floor-pivot s1bounce / r1reject articles (failed) and obos-levels. Stated change: Camarilla
geometry with a pre-declared range-day gate (open inside L3..H3) and a quiet-index gate. Sibling of
pod-cpr-wide-range-day-pivot-fade (different levels and gate). Side: LONG (this file); the SHORT mirror at H3 is
pod-camarilla-l3-quiet-fade-short.

Levels (prior completed day only): C = D-1 close = today's open / (1 + gap%); today's open = close / (1 + fromOpen%);
PDH = close + dist_pdh_atr x atr_d, PDL = close - dist_pdl_atr x atr_d (taken from the symbol-day's first frame row);
R = PDH - PDL; L1/H1 = C -/+ 1.1 R/12, L3/H3 = C -/+ 1.1 R/4, L4/H4 = C -/+ 1.1 R/2.
Rules (plain English; long shown, short = mirror at H3 / H4 / H1 with rsi5 >= 65):
  1. Today's open is strictly between L3 and H3.
  2. Quiet index: |spy_fo| <= 0.4% at the signal bar.
  3. First L3 test today: this bar's low <= L3 while the low of day before this bar was above L3 (includes the
     09:30-09:45 bars through dist_lod_atr), the bar closes back above L3, and the low of day is still above L4.
  4. rsi5 <= 35.
  Entry: that close, bar close 10:00-14:30. Stop (GEOM S): L4 - 0.02 x atr_d. Target: L1 (nearer than C); skip when
  L1 is less than 0.5R above the entry. Flat 15:55. Costs per config/default.yaml (scorer).
Pre-declared choices: none beyond the source values (the target rule 'C or L1 if nearer' always resolves to L1).
No tweak used. No tuning on valid.
Educational only - not financial advice."""
SIDE = "long"
GEOM = "S"
WINDOW = (1000, 1430)
CONTEXT = ["spy_fo"]
LAYERS = ["open inside Camarilla L3..H3 (D-1 H/L/C)", "|spy_fo| <= 0.4%",
          "first L3 test today: low <= L3, close > L3, LOD above L4", "rsi5 <= 35",
          "stop L4 - 0.02 ATR, target L1 (>= 0.5R)", "10:00-14:30 ET"]

import numpy as np
import pandas as pd

_ST = {}


def _f(df, c):
    return df[c].to_numpy(float) if c in df else np.full(len(df), np.nan)


def _key(df):
    s = pd.Series(df["symbol"].astype(str).to_numpy()) + "|" + pd.Series(df["date"].astype(str).to_numpy())
    return pd.factorize(s)[0]


def _start(k):
    return np.r_[True, k[1:] != k[:-1]]


def _dayfirst(x, k):
    st = _start(k)
    return np.asarray(x, float)[st][np.cumsum(st) - 1]


def _lag(x, k, n=1):
    x = np.asarray(x, float)
    p = np.full(len(x), np.nan)
    if len(x) > n:
        p[n:] = x[:-n]
        p[n:][k[n:] != k[:-n]] = np.nan
    return p


def levels(df, k):
    c, atr = _f(df, "close"), _f(df, "atr_d")
    op = _dayfirst(c / (1 + _f(df, "fromOpen") / 100), k)
    pc = op / (1 + _dayfirst(_f(df, "gap"), k) / 100)
    pdh = _dayfirst(c + _f(df, "dist_pdh_atr") * atr, k)
    pdl = _dayfirst(c - _f(df, "dist_pdl_atr") * atr, k)
    R = pdh - pdl
    return op, pc, pdh, pdl, R


def mask(df) -> np.ndarray:
    _ST.clear()
    if not len(df) or "spy_fo" not in df:
        return np.zeros(len(df), dtype=bool)
    k = _key(df)
    tod = df["tod"].to_numpy(np.int64)
    c, h, l, atr = _f(df, "close"), _f(df, "high"), _f(df, "low"), _f(df, "atr_d")
    with np.errstate(invalid="ignore", divide="ignore"):
        op, pc, pdh, pdl, R = levels(df, k)
        L1, L3, L4 = pc - 1.1 * R / 12, pc - 1.1 * R / 4, pc - 1.1 * R / 2
        H1, H3, H4 = pc + 1.1 * R / 12, pc + 1.1 * R / 4, pc + 1.1 * R / 2
        m = (R > 0) & (op > L3) & (op < H3) & (np.abs(_f(df, "spy_fo")) <= 0.4)
        m &= (tod >= WINDOW[0]) & (tod <= WINDOW[1])
        if SIDE == "long":
            lod = c - _f(df, "dist_lod_atr") * atr
            m &= (l <= L3) & (_lag(lod, k) > L3) & (c > L3) & (lod > L4) & (_f(df, "rsi5") <= 35)
            stop = L4 - 0.02 * atr
            tgt = L1
            m &= (tgt - c) >= 0.5 * (c - stop)
        else:
            hod = c + _f(df, "dist_hod_atr") * atr
            m &= (h >= H3) & (_lag(hod, k) < H3) & (c < H3) & (hod < H4) & (_f(df, "rsi5") >= 65)
            stop = H4 + 0.02 * atr
            tgt = H1
            m &= (c - tgt) >= 0.5 * (stop - c)
    _ST[id(df)] = (stop, tgt)
    return np.asarray(m, dtype=bool)


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
