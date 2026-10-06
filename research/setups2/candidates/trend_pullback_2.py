"""trend_pullback #2 -- sell the rip in a stock trending down from the open (first trading hour).

Educational only -- not financial advice.
Asymmetric version (target +1R / stop -0.5R). The same mask is used by trend_pullback_1/2/3; only the exit geometry differs.
Short when a stock that is down from the open and below VWAP and its 5-min SMA50 bounces back above its
5-min SMA20, between 09:50 and 10:30 ET. Train/valid numbers: see research/setups2/notes/trend_pullback.md.
"""
import numpy as np

SIDE = "short"
GEOM = "t1s05"
LAYERS = [
    "Down from the open: fromOpen < -0.5%",
    "Still below VWAP and below the 5-min SMA50 (downtrend context)",
    "Bounce: close back above the 5-min SMA20 (sma20_dist_pct > 0)",
    "Bar close at or before 10:30 ET",
]


def mask(df) -> np.ndarray:
    with np.errstate(invalid="ignore"):
        m = (
            (df["fromOpen"].to_numpy() < -0.5)
            & (df["vwapDistPct"].to_numpy() < 0)
            & (df["sma50_dist_pct"].to_numpy() < 0)
            & (df["sma20_dist_pct"].to_numpy() > 0)
            & (df["tod"].to_numpy() <= 1030)
        )
    return np.asarray(m, dtype=bool)
