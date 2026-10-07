"""MF-flowsell-momalign-rsi5hi - MarcoFlow rule stack 'flow-sell+mom-aligned+rsi5-high' re-scored on the setup lab (short, t1s05).
Source: MarcoFlow StrategyReview recommendations (best Wilson LB 67.9, 21 signals, signal-level only).
Lab (1c/side): train exp_r +0.0340R (n 164, day-t 0.6), valid exp_r +0.1887R (n 51, day-t 1.7),
valid at production cost (+1bps/side, +2c stops, no extended-tier surcharge) +0.1224R.
Research finalist only: NOT live until the lead's locked-holdout scoring and the backlog/ledger process.
Educational only - not financial advice."""
import numpy as np

SIDE = "short"
GEOM = "t1s05"
LAYERS = [
    "heat <= -30 (a MarcoFlow bearish heat signal; direction = sign of heat)",
    "buyPressure < -0.25 (signed volume, 19 bars; MarcoFlow flow-sell)",
    "RSI(14) fell > 1 point over 3 bars (MarcoFlow mom-aligned, short)",
    "RSI(5) > 70 (MarcoFlow rsi5-high)",
    "time window 09:50-15:00 ET (lab frame)",
]


def mask(df) -> np.ndarray:
    heat = df["heat"].to_numpy(dtype=float)
    buyPressure = df["buyPressure"].to_numpy(dtype=float)
    rsi5 = df["rsi5"].to_numpy(dtype=float)
    rsi = df["rsi"].to_numpy(dtype=float)
    rsiSlope = df["rsiSlope"].to_numpy(dtype=float)
    with np.errstate(invalid="ignore"):
        return (heat <= -30) & (buyPressure < -0.25) & (rsiSlope < -1) & (rsi5 > 70)
