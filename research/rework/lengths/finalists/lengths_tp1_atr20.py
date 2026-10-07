"""Finalist (rework key: lengths, WEAK) -- trend_pullback_1 (failed on test: +0.015R) with daily ATR 20 (was 14).

Educational only -- not financial advice.
Same mask as the parent (fromOpen < -0.5%, below VWAP and SMA50, above SMA20, bar close <= 10:30); only R changes
(R = 0.25 x ATR(20)), short t05s1.
Train 2026-07-15..08-25: n512 exp +0.064R t0.85. Valid: n203 exp +0.061R t1.68, ex-best-day +0.047R (train ex-best-day +0.006R), baseline -0.046R.
Plateau valid mean +0.006R and NOT all neighbours positive -- passes the pre-declared gate only on the mean;
the identical trade list already failed the setups2 test. Expect it to fail.
"""
import numpy as np

SIDE, GEOM, ATR = "short", "t05s1", 20
R_COL = "r_short_t05s1_a20"


def mask(df) -> np.ndarray:
    with np.errstate(invalid="ignore"):
        return ((df["fromOpen"].to_numpy() < -0.5) & (df["vwapDistPct"].to_numpy() < 0) & (df["smad_50"].to_numpy() < 0)
                & (df["smad_20"].to_numpy() > 0) & (df["tod"].to_numpy() <= 1030))
