"""pod-smb-day2-compression-afternoon-break-long - Second-day play: a quiet day-2 compression, afternoon break of the
day-2 morning high (LONG).

Source: SMB Capital 'The Explosive Second Day Play' (Bellafiore / SMB Training; day-1 levels drive day 2).
URL: https://smbtraining.com/blog/tag/day

VARIANT of the already-tested SMB Second-Day Play (pod-smb-day2-drive-pullback-long trades the day-2 open drive).
Stated changes: day 2 must be quiet (compression) and the entry is a 13:00-15:00 break, not the morning.

Rules (plain English, LONG):
  Day 1 (D-1, completed day, lib.daily()): return >= +4%, volume >= 3 x the mean of the 20 sessions before, close in the
  top 30% of its range.
  Day 2:
  1. The 09:30-12:30 range (running high / low of day at the 12:30 bar) <= 45% of the day-1 range.
  2. The day-2 low so far (at the signal bar) stays above the day-1 midpoint.
  3. The 12:55 bar closes above session VWAP.
  4. Between 13:00 and 15:00 a 5m close above the 09:30-12:30 high with volumeRatio (bar volume / 20-bar average)
     >= 1.5. The first such bar is taken.
  Entry: that close (= next bar open). Stop (GEOM S): the lower of VWAP and the low of the last 6 bars (signal bar
  included), minus 0.1 x ATR(5m). Target: the day-1 high, or 2R when the entry is already at / above it. Flat 15:55.
No tweak made. Costs per config/default.yaml (applied by the scorer).
Educational only - not financial advice."""
SIDE = "long"
GEOM = "S"
WINDOW = (1300, 1500)
LAYERS = ["D-1 ret >= 4%, rvol >= 3, close top 30%", "09:30-12:30 range <= 45% of D-1 range",
          "low so far > D-1 midpoint", "12:55 close > VWAP", "13:00-15:00 close > morning high, volumeRatio >= 1.5",
          "stop min(VWAP, 6-bar low) - 0.1 ATR5m, target D-1 high or 2R"]

import numpy as np
import pandas as pd

import _cwt3_bars as C
import _r24_bars as R

_ST = {}


def _compute(df):
    n = len(df)
    z = np.zeros(n, bool), np.full(n, np.nan), np.full(n, np.nan)
    if not n:
        return z
    b = C.base(df)
    k = C.key(df)
    tod, c = b["tod"], b["c"]
    d = R.daymap(df, ["ret1", "rvol1", "clpos1", "high1", "low1"], R.daily_feats())
    mh = C.at_tod(b["hod"], k, tod, 1230)
    ml = C.at_tod(b["lod"], k, tod, 1230)
    v1255 = C.at_tod(c - b["vwap"], k, tod, 1255)
    l6 = b["l"].copy()
    for j in range(1, 6):
        l6 = np.fmin(l6, C.lag(b["l"], k, j)) if j else l6
    l6[np.isnan(C.lag(b["l"], k, 5))] = np.nan                     # needs 6 bars of the same day
    with np.errstate(invalid="ignore", divide="ignore"):
        r1 = d["high1"] - d["low1"]
        m = (d["ret1"] >= 0.04) & (d["rvol1"] >= 3) & (d["clpos1"] >= 0.7)
        m &= (mh - ml) <= 0.45 * r1                                                         # (1)
        m &= b["lod"] > 0.5 * (d["high1"] + d["low1"])                                     # (2)
        m &= v1255 > 0                                                                      # (3)
        m &= (tod >= 1300) & (tod <= 1500)
        m &= (c > mh) & (C.f(df, "volumeRatio") >= 1.5)                                     # (4)
        sp = np.minimum(b["vwap"], l6) - 0.1 * b["atr5"]
        m &= sp < c
        tg = np.where(d["high1"] > c, d["high1"], c + 2 * (c - sp))
    return np.asarray(m, bool), sp, tg


def mask(df) -> np.ndarray:
    try:
        m, stop, tgt = _compute(df)
    except (KeyError, FileNotFoundError):
        m, stop, tgt = np.zeros(len(df), bool), np.full(len(df), np.nan), np.full(len(df), np.nan)
    _ST.clear()
    _ST[id(df)] = (stop, tgt)
    return np.asarray(m, bool)


def _get(f):
    s = _ST.get(id(f))
    if s is None or len(s[0]) != len(f):
        mask(f)
        s = _ST[id(f)]
    return s


def stop_price(f, i):
    return float(_get(f)[0][i])


def target_price(f, i, stop):
    return float(_get(f)[1][i])
