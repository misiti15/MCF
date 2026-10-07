"""Finalist (rework key: lengths) -- volume_flip_2 (failed on test: +0.030R, win 67% below breakeven) with
short RSI 3 (was 5) and 5-min SMA10 distance (was SMA20). ATR 14, RSI(14) divergence unchanged.

Educational only -- not financial advice.
Rule: rsis_3 > 90, close > 1% above 5-min SMA10, bear_div on RSI(14), 13:00-15:00 ET bar close; short t05s1
(+0.5R / -1R), R = 0.25 x ATR(14).
Train 2026-07-15..08-25: n517 exp +0.139R t1.90. Valid 08-26..09-15: n88 exp +0.113R t1.79, ex-best-day +0.085R (train ex-best-day only +0.051R),
random-symbol same-time baseline -0.030R. Plateau (one-step neighbours) valid mean +0.078R, all positive.
Caveat: lineage already used holdout look 1 (setups2 test), so look 2 needs t >= 1.5; 65/88 valid trades shared
with the parent mask.
"""
import numpy as np

SIDE, GEOM, ATR = "short", "t05s1", 14
R_COL = "r_short_t05s1_a14"


def mask(df) -> np.ndarray:
    tod = df["tod"].to_numpy()
    return ((df["rsis_3"].to_numpy() > 90) & (df["smad_10"].to_numpy() > 1.0) & (df["bear_div_14"].to_numpy() > 0)
            & (tod >= 1300) & (tod <= 1500))
