"""Finalist (rework key: lengths) -- exhaustion_short / volume_flip_1 with short RSI 7 (was 5) and daily ATR 20 (was 14).

Educational only -- not financial advice.
Parent: research/setups2/candidates/volume_flip_1.py (live on paper). Thresholds unchanged; only lengths move.
Rule: rsis_7 > 90, close > 1% above 5-min SMA20, bear_div on RSI(14), 13:00-15:00 ET bar close; short t1s1, R = 0.25 x ATR(20).
Train 2026-07-15..08-25: n398 exp +0.190R t1.42. Valid 08-26..09-15: n90 exp +0.184R t2.03, ex-best-day +0.134R (train ex-best-day +0.079R),
random-symbol same-time baseline +0.032R. Plateau (7 one-step neighbours) valid mean +0.143R, all positive.
Caveat: 345/398 train and 69/90 valid trades are shared with the live base rule; not distinguishable from the base.
Frame: research/rework/lengths/build.py (full config costs).
"""
import numpy as np

SIDE, GEOM, ATR = "short", "t1s1", 20
R_COL = "r_short_t1s1_a20"
NEIGHBORS = ["rsis5,rsi14,fast20,atr20", "rsis10,rsi14,fast20,atr20", "rsis7,rsi10,fast20,atr20",
             "rsis7,rsi21,fast20,atr20", "rsis7,rsi14,fast10,atr20", "rsis7,rsi14,fast50,atr20", "rsis7,rsi14,fast20,atr14"]


def mask(df) -> np.ndarray:
    tod = df["tod"].to_numpy()
    return ((df["rsis_7"].to_numpy() > 90) & (df["smad_20"].to_numpy() > 1.0) & (df["bear_div_14"].to_numpy() > 0)
            & (tod >= 1300) & (tod <= 1500))
