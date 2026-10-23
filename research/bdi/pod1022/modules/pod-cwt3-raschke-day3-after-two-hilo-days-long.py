"""pod-cwt3-raschke-day3-after-two-hilo-days-long - Day-3 long after two high-to-low (open-high, close-low) days inside
a 20-day range.

Source: Chat With Traders EP048, Linda Raschke (day-3 bias after two consecutive range-extreme days inside a 20-day
range) [~00:30:42-00:34:46].
URL: https://chatwithtraders.com/048

VARIANT of cwt-c-c7-index-streak (Raschke day-3 SHORT after two low-to-high days, daily-close entry, failed). Stated
changes: the mirror side (long after two high-to-low days) and an intraday entry trigger instead of a daily-close entry.

Rules (plain English, LONG). Universe: the scorer universe with adv20 >= $100M (index / sector ETFs and liquid large
caps; pre-declared liquidity floor, not tuned).
  Daily setup, known before the open (completed days only):
  (1) days D-1 and D-2 each open in the top 30% of their range ((open - low) / (high - low) >= 0.70) and close in the
      bottom 25% ((close - low) / (high - low) <= 0.25);
  (2) D-1 close > the 20-day low and < the 20-day high of the 20 sessions before D-1 (inside the range, no breakdown).
  (The optional 3-10 oscillator filter is not used.)
  Day 3 on 5m bars, bar close 10:05-12:30 ET:
  (3) after the 30-minute opening range (09:30-10:00, read from the running high / low of day at the 10:00 bar, which
      includes 09:30-09:45), buy on the first 5m close above the opening-range high OR above the prior-day close,
      whichever comes first;
  (4) the session low so far is still >= the 09:30-10:00 low (the early push down held).
  Entry: that bar's close. Stop (GEOM S): session low - 0.05%. Target: the prior-day high or 1.5R, whichever is nearer
  (1.5R when the prior-day high is not above the entry); else flat 15:55. One trade per symbol per day (scorer).
No tweak made. Costs per config/default.yaml (applied by the scorer). Only bars up to the decision bar and completed
daily bars are used.
Educational only - not financial advice."""
import importlib.util
import sys
from pathlib import Path

import numpy as np

SIDE = "long"
GEOM = "S"
WINDOW = (1005, 1230)
MIN_ADV = 100e6
CONTEXT = []
LAYERS = ["D-1 and D-2 open top 30% / close bottom 25% of range", "D-1 close inside the prior 20-day range",
          "first 5m close above the 30m OR high or the prior close, 10:05-12:30",
          "session low >= the 09:30-10:00 low", "stop LOD - 0.05%, target min(PDH, 1.5R)"]

_ST = {}


def _u():
    n = "_cwt3_bars"
    if n not in sys.modules:
        sp = importlib.util.spec_from_file_location(n, Path(__file__).resolve().parent / "_cwt3_bars.py")
        m = importlib.util.module_from_spec(sp)
        sys.modules[n] = m
        sp.loader.exec_module(m)
    return sys.modules[n]


def _compute(df):
    U = _u()
    n = len(df)
    z0 = (np.zeros(n, bool), np.full(n, np.nan), np.full(n, np.nan))
    if not n:
        return z0
    b = U.base(df)
    k = U.key(df)
    c, tod, lod, hod, pc, pdh = b["c"], b["tod"], b["lod"], b["hod"], b["pc"], b["pdh"]
    d = U.map_daily(df, k, ["d_openpos_1", "d_closepos_1", "d_openpos_2", "d_closepos_2", "d_close_1",
                            "hi20_prev_1", "lo20_prev_1"])
    with np.errstate(invalid="ignore", divide="ignore"):
        g = (d["d_openpos_1"] >= 0.70) & (d["d_closepos_1"] <= 0.25)                  # (1) D-1
        g &= (d["d_openpos_2"] >= 0.70) & (d["d_closepos_2"] <= 0.25)                 # (1) D-2
        g &= (d["d_close_1"] > d["lo20_prev_1"]) & (d["d_close_1"] < d["hi20_prev_1"])  # (2)
        orh = U.at_tod(hod, k, tod, 1000)
        orl = U.at_tod(lod, k, tod, 1000)
        m = g & (tod >= WINDOW[0]) & (tod <= WINDOW[1])
        m &= (c > orh) | (c > pc)                                                     # (3)
        m &= lod >= orl - 1e-9 * c                                                    # (4)
        stop = lod * (1 - 0.0005)
        r = c - stop
        tgt = np.where(pdh > c, np.fmin(pdh, c + 1.5 * r), c + 1.5 * r)
        m &= np.isfinite(stop) & np.isfinite(tgt) & (stop < c) & (tgt > c)
    return m, stop, tgt


def mask(df) -> np.ndarray:
    try:
        m, stop, tgt = _compute(df)
    except KeyError:
        n = len(df)
        m, stop, tgt = np.zeros(n, bool), np.full(n, np.nan), np.full(n, np.nan)
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
