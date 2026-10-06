"""win_geometry #3 -- best HIGH-WIN-RATE (t05s1) finalist: sharp RSI thrust in a stock deep below trend.

Educational only -- not financial advice.
Train: n=665, 16.6/day, win 74.6%, exp +0.166R, PF 1.88.  Valid: n=100, win 68.0%, exp +0.020R, PF 1.07
(baseline long t05s1 -0.100). Breakeven win rate for t05s1 after costs ~0.70. NOT viable: valid win rate
fell below breakeven-plus-margin. Included only as the strongest representative of the high-win family.
"""
import numpy as np

SIDE = "long"
GEOM = "t05s1"
LAYERS = [
    "MACD deeply negative (macdPct < -1.06): stock is in a downtrend",
    "RSI(14) jumped more than 23.7 points over 3 bars (rsiSlope > 23.7)",
    "Momentum turned positive (momentum > 0.569)",
]


def mask(df) -> np.ndarray:
    with np.errstate(invalid="ignore"):
        m = (
            (df["macdPct"].to_numpy() < -1.06)
            & (df["rsiSlope"].to_numpy() > 23.7)
            & (df["momentum"].to_numpy() > 0.569)
        )
    return np.asarray(m, dtype=bool)
