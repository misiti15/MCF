"""MF-rsimid-flowsell-momfall - MarcoFlow rule stack 'rsi-mid+flow-sell+mom-falling' re-scored on the setup lab (short, t1s05).
Source: MarcoFlow StrategyReview recommendations (best Wilson LB 66, 60 signals, signal-level only).
Lab (1c/side): train exp_r +0.0140R (n 921, day-t 0.31), valid exp_r +0.1057R (n 239, day-t 1.71),
valid at production cost (+1bps/side, +2c stops, no extended-tier surcharge) +0.0683R.
Research finalist only: NOT live until the lead's locked-holdout scoring and the backlog/ledger process.
Educational only - not financial advice."""
import numpy as np

SIDE = "short"
GEOM = "t1s05"
LAYERS = [
    "heat <= -30 (a MarcoFlow bearish heat signal; direction = sign of heat)",
    "35 <= RSI(14) <= 65 (MarcoFlow rsi-mid)",
    "buyPressure < -0.25 (signed volume, 19 bars; MarcoFlow flow-sell)",
    "RSI(14) fell > 1 point over 3 bars (MarcoFlow mom-falling)",
    "time window 09:50-15:00 ET (lab frame)",
]


def mask(df) -> np.ndarray:
    heat = df["heat"].to_numpy(dtype=float)
    buyPressure = df["buyPressure"].to_numpy(dtype=float)
    rsi = df["rsi"].to_numpy(dtype=float)
    rsiSlope = df["rsiSlope"].to_numpy(dtype=float)
    with np.errstate(invalid="ignore"):
        return (heat <= -30) & (rsi >= 35) & (rsi <= 65) & (buyPressure < -0.25) & (rsiSlope < -1)
