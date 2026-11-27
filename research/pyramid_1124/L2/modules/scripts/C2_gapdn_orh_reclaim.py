"""L2-C2 gap-down opening-range-high reclaim long (buy the gap-down name when the short side's thesis fails).
Needs the 09:30-09:45 head rows (cwt=True). OR20 high = max high of bars ending 09:35..09:50. Signal: first 5-min close
above OR20 high (prior close <= OR20 high), 10:00-12:00, close above VWAP, gap <= -G% and gap_atr <= -A.
Params via module globals GAP_PCT, GAP_ATR, GATE. Educational only - not financial advice."""
import numpy as np
import pandas as pd
from l2common import gate_g

SIDE = "long"
GEOM = "t1s1"
GAP_PCT, GAP_ATR, GATE = -1.5, -0.5, False
W = (1000, 1200)


def mask(df):
    tod = df["tod"].to_numpy(int)
    key = df["symbol"].astype(str) + "|" + df["date"].astype(str)
    hi = df["high"].astype(float)
    orh = hi.where(tod <= 950).groupby(key.values).transform("max").to_numpy(float)
    c = df["close"].to_numpy(float)
    pc = df.groupby(key.values)["close"].shift(1).to_numpy(float)
    gap = df["gap"].to_numpy(float)
    atr = df["atr_d"].to_numpy(float)
    fo = df["fromOpen"].to_numpy(float)
    with np.errstate(invalid="ignore", divide="ignore"):
        o_open = c / (1 + fo / 100)
        prevc = o_open / (1 + gap / 100)
        gap_atr = (o_open - prevc) / atr
        m = (tod >= W[0]) & (tod <= W[1]) & (c > orh) & (pc <= orh) & (df["vwapDistPct"].to_numpy(float) > 0)
        m &= (gap <= GAP_PCT) & (gap_atr <= GAP_ATR)
    if GATE:
        m &= gate_g(df)
    return np.asarray(m, bool)
