"""obos_levels #1 -- oversold failed-breakdown hammer at the prior-day low that FAILS (continuation short).

Educational only -- not financial advice.
Train (40 sessions): n=541, win 52.5%, exp +0.146R, PF 1.39 (halves +0.239 / +0.038).
Valid (15 sessions): n=219, win 47.5%, exp +0.067R, PF 1.16 (baseline short t1s1 +0.020). Marginal: SE 0.062.
Breakeven win rate for t1s1 after costs ~ 0.50-0.52.
"""
import numpy as np

SIDE = "short"
GEOM = "t1s1"
LAYERS = [
    "RSI(14) < 25 (oversold)",
    "Failed break of prior-day low: bar low <= PDL and close back above PDL by 0 to 0.2 daily ATR",
    "Lower wick >= 50% of bar range (hammer-looking rejection)",
    "Bar close at or before 11:30 ET",
]


def mask(df) -> np.ndarray:
    close = df["close"].to_numpy(np.float64)
    low = df["low"].to_numpy(np.float64)
    atr = df["atr_d"].to_numpy(np.float64)
    dpl = df["dist_pdl_atr"].to_numpy(np.float64)
    pdl = close - dpl * atr
    with np.errstate(invalid="ignore"):
        m = (
            (df["rsi"].to_numpy() < 25)
            & (low <= pdl) & (dpl > 0) & (dpl <= 0.2)
            & (df["lower_wick"].to_numpy() >= 0.5)
            & (df["tod"].to_numpy() <= 1130)
        )
    return np.asarray(m, dtype=bool)
