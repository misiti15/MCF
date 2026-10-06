"""volume_flip #1 - afternoon bearish RSI divergence after an extended run (short, t1s1).
Educational only - not financial advice."""
import numpy as np

SIDE = "short"
GEOM = "t1s1"
LAYERS = [
    "rsi5 > 90 (short-term overbought)",
    "sma20_dist_pct > 1.0 (close > 1% above 5-min SMA20)",
    "bear_div == 1 (price at 20-bar high while RSI(14) is >5 below its 20-bar max)",
    "time window 13:00-15:00 ET (bar close)",
]


def mask(df) -> np.ndarray:
    rsi5 = df["rsi5"].to_numpy(dtype=float)
    sma20 = df["sma20_dist_pct"].to_numpy(dtype=float)
    div = df["bear_div"].to_numpy(dtype=float)
    tod = df["tod"].to_numpy(dtype=float)
    return (rsi5 > 90) & (sma20 > 1.0) & (div > 0) & (tod >= 1300) & (tod <= 1500)
