"""MF-rsimidlo-flowalign-momalign - MarcoFlow rule stack 'rsi-mid-low+flow-aligned+mom-aligned' re-scored on the setup lab (short, t1s05).
Source: MarcoFlow StrategyReview recommendations (best Wilson LB 67.6, 43 signals, signal-level only).
Lab (1c/side): train exp_r +0.0154R (n 530, day-t 0.3), valid exp_r +0.1227R (n 154, day-t 1.84),
valid at production cost (+1bps/side, +2c stops, no extended-tier surcharge) +0.0886R.
Research finalist only: NOT live until the lead's locked-holdout scoring and the backlog/ledger process.
Educational only - not financial advice."""
import numpy as np

SIDE = "short"
GEOM = "t1s05"
LAYERS = [
    "heat <= -30 (a MarcoFlow bearish heat signal; direction = sign of heat)",
    "45 <= RSI(14) < 55 (MarcoFlow rsi-mid-low)",
    "buyPressure < -0.15 (MarcoFlow flow-aligned, short)",
    "RSI(14) fell > 1 point over 3 bars (MarcoFlow mom-aligned, short)",
    "time window 09:50-15:00 ET (lab frame)",
]


def mask(df) -> np.ndarray:
    heat = df["heat"].to_numpy(dtype=float)
    buyPressure = df["buyPressure"].to_numpy(dtype=float)
    rsi = df["rsi"].to_numpy(dtype=float)
    rsiSlope = df["rsiSlope"].to_numpy(dtype=float)
    with np.errstate(invalid="ignore"):
        return (heat <= -30) & (rsi >= 45) & (rsi < 55) & (buyPressure < -0.15) & (rsiSlope < -1)
