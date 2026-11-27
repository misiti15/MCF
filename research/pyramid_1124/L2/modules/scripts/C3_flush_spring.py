"""L2-C3 gap-down flush-spring long: in a gapped-down name that is >= 0.5 daily ATR below its open, a climax bar
(volumeRatio >= VR) that set the low of day is followed by a bar closing above that climax bar's high. 10:00-14:30.
Needs head rows (cwt=True) so the low of day includes 09:30-09:50. Educational only - not financial advice."""
import numpy as np
import pandas as pd
from l2common import gate_g

SIDE = "long"
GEOM = "t1s1"
VR, GATE = 2.0, False
W = (1000, 1430)


def mask(df):
    tod = df["tod"].to_numpy(int)
    kv = (df["symbol"].astype(str) + "|" + df["date"].astype(str)).values
    g = df.groupby(kv)
    lo = df["low"].astype(float)
    lod = lo.groupby(kv).cummin()
    p_low = g["low"].shift(1).to_numpy(float)
    p_high = g["high"].shift(1).to_numpy(float)
    p_close = g["close"].shift(1).to_numpy(float)
    p_lod = lod.groupby(kv).shift(1).to_numpy(float)           # LOD through the prior bar
    p_vr = g["volumeRatio"].shift(1).to_numpy(float)
    c = df["close"].to_numpy(float)
    gap = df["gap"].to_numpy(float)
    atr = df["atr_d"].to_numpy(float)
    fo = df["fromOpen"].to_numpy(float)
    with np.errstate(invalid="ignore", divide="ignore"):
        o_open = c / (1 + fo / 100)
        prevc = o_open / (1 + gap / 100)
        gap_atr = (o_open - prevc) / atr
        p_from_open_atr = (p_close - o_open) / atr
        m = (tod >= W[0]) & (tod <= W[1]) & (gap_atr <= -0.5) & (p_low <= p_lod + 1e-9) & (p_vr >= VR)
        m &= (c > p_high) & (p_from_open_atr <= -0.5)
    if GATE:
        m &= gate_g(df)
    return np.asarray(m, bool)
