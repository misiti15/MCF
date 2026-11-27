"""Base-rate random-entry controls (no look-ahead: day-level filter known at the bar + one random bar in the window).
KIND set by the harness. Educational only - not financial advice."""
import zlib
import numpy as np, pandas as pd
from l2common import gate_g
SIDE, GEOM, KIND = "long", "t1s1", "C1"
ETF = None


def mask(df):
    tod = df["tod"].to_numpy(int)
    gap = df["gap"].to_numpy(float); atr = df["atr_d"].to_numpy(float); c = df["close"].to_numpy(float)
    fo = df["fromOpen"].to_numpy(float)
    with np.errstate(invalid="ignore", divide="ignore"):
        o = c / (1 + fo / 100); pc = o / (1 + gap / 100); ga = (o - pc) / atr
        if KIND == "C1":
            m = (ga <= -0.4056) & (tod >= 1050) & (tod <= 1055)
        elif KIND == "C2":
            m = (gap <= -1.5) & (ga <= -0.5) & (tod >= 1000) & (tod <= 1200)
        elif KIND == "C3":
            m = (ga <= -0.5) & (tod >= 1000) & (tod <= 1430)
        else:
            m = df["symbol"].astype(str).isin(ETF).to_numpy() & (atr / c * 100 >= 3.5967583179473883) & (tod >= 1400) & (tod <= 1500) & gate_g(df)
    m &= np.isfinite(atr)
    key = (df["symbol"].astype(str) + "|" + df["date"].astype(str)).to_numpy()
    out = np.zeros(len(df), bool)
    idx = np.flatnonzero(m)
    if not len(idx):
        return out
    for k, g in pd.Series(idx).groupby(key[idx]):
        out[g.values[np.random.default_rng(zlib.crc32(("b" + k).encode())).integers(len(g))]] = True
    return out
