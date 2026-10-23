"""pod-camarilla-h4-trendday-break-short - Camarilla L4 breakdown from an inside-band open (SHORT).

Source: Camarilla equation (Nick Scott); LuxAlgo concept library 'Camarilla' (H4/L4 = trend-day trigger, H5/L5 =
target).
URL: https://www.luxalgo.com/library/concept/camarilla.md

VARIANT of CWT10 PDH breakout (failed) and R17 prior-day retest (failed). Stated change: the level is
H4 = C + 1.1 x (PDH - PDL)/2, only after an open inside the H3-L3 band (no gap-and-go), with a breadth gate. Regime
partner of pod-camarilla-l3-quiet-fade. Side: SHORT (this file; the L4 mirror, target L5); the long is
pod-camarilla-h4-trendday-break-long.

Levels (prior completed day only): C = D-1 close = today's open / (1 + gap%); open = close / (1 + fromOpen%);
PDH / PDL from dist_pdh_atr / dist_pdl_atr (first frame row of the symbol-day); R = PDH - PDL;
H3/L3 = C +/- 1.1 R/4, H4/L4 = C +/- 1.1 R/2, H5 = (PDH / PDL) x C, L5 = C - (H5 - C).
Rules (plain English; long shown, short = mirror below L4 with breadth <= 0.45, qqq_vwap < 0, close < VWAP):
  1. Today's open is strictly between L3 and H3.
  2. This bar is the first 5m close above H4 today (frame bars from 09:50), bar close 10:00-13:30, volumeRatio >= 1.5.
  3. breadth >= 0.55 and qqq_vwap > 0; close above the session VWAP.
  Entry: that close. Stop (GEOM S): H3; skip when H4 - H3 > 1.2 x atr_d. Target: H5 (skip if not above the entry).
  Flat 15:55. Costs per config/default.yaml (scorer).
Pre-declared choices: the source's 'else holdtr' fallback cannot be expressed with a structural stop here; H5 is
always defined (PDL > 0), so every trade uses the H5 limit. No tweak used. No tuning on valid.
Educational only - not financial advice."""
SIDE = "short"
GEOM = "S"
WINDOW = (1000, 1330)
CONTEXT = ["breadth", "qqq_vwap"]
LAYERS = ["open inside Camarilla L3..H3", "first close above H4 today, volumeRatio >= 1.5",
          "breadth >= 0.55, qqq_vwap > 0, close > VWAP", "stop H3 (skip H4-H3 > 1.2 ATR), target H5",
          "10:00-13:30 ET"]

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


def _gcum(x, k):
    x = np.asarray(x, float)
    cs = np.cumsum(x)
    st = _start(k)
    base = (cs - x)[st]
    return cs - base[np.cumsum(st) - 1]


def mask(df) -> np.ndarray:
    _ST.clear()
    if not len(df) or "breadth" not in df or "qqq_vwap" not in df:
        return np.zeros(len(df), dtype=bool)
    k = _key(df)
    tod = df["tod"].to_numpy(np.int64)
    c, atr = _f(df, "close"), _f(df, "atr_d")
    with np.errstate(invalid="ignore", divide="ignore"):
        op = _dayfirst(c / (1 + _f(df, "fromOpen") / 100), k)
        pc = op / (1 + _dayfirst(_f(df, "gap"), k) / 100)
        pdh = _dayfirst(c + _f(df, "dist_pdh_atr") * atr, k)
        pdl = _dayfirst(c - _f(df, "dist_pdl_atr") * atr, k)
        R = pdh - pdl
        H3, L3 = pc + 1.1 * R / 4, pc - 1.1 * R / 4
        H4, L4 = pc + 1.1 * R / 2, pc - 1.1 * R / 2
        H5 = pdh / pdl * pc
        L5 = pc - (H5 - pc)
        m = (R > 0) & (pdl > 0) & (op > L3) & (op < H3) & ((H4 - H3) <= 1.2 * atr)
        m &= (tod >= WINDOW[0]) & (tod <= WINDOW[1]) & (_f(df, "volumeRatio") >= 1.5)
        br, qv, vd = _f(df, "breadth"), _f(df, "qqq_vwap"), _f(df, "vwapDistPct")
        if SIDE == "long":
            x = c > H4
            m &= (br >= 0.55) & (qv > 0) & (vd > 0)
            stop, tgt = H3, H5
            m &= tgt > c
        else:
            x = c < L4
            m &= (br <= 0.45) & (qv < 0) & (vd < 0)
            stop, tgt = L3, L5
            m &= tgt < c
        m &= x & ((_gcum(x, k) - x) == 0)          # the first close beyond the level today
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
