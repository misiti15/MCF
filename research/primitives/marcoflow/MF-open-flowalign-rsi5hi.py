"""MF-open-flowalign-rsi5hi - MarcoFlow rule stack 'open-after20+flow-aligned+rsi5-high' re-scored on the setup lab (short, t1s1).
Source: MarcoFlow StrategyReview recommendations (best Wilson LB 62, 39 signals, signal-level only).
Lab (1c/side): train exp_r +0.0590R (n 889, day-t 0.81), valid exp_r +0.1753R (n 200, day-t 1.68),
valid at production cost (+1bps/side, +2c stops, no extended-tier surcharge) +0.1061R.
Research finalist only: NOT live until the lead's locked-holdout scoring and the backlog/ledger process.
Educational only - not financial advice."""
import numpy as np

SIDE = "short"
GEOM = "t1s1"
LAYERS = [
    "heat <= -30 (a MarcoFlow bearish heat signal; direction = sign of heat)",
    "bar close 09:50-10:55 ET (MarcoFlow open-after20)",
    "buyPressure < -0.15 (MarcoFlow flow-aligned, short)",
    "RSI(5) > 70 (MarcoFlow rsi5-high)",
]


def mask(df) -> np.ndarray:
    heat = df["heat"].to_numpy(dtype=float)
    tod = df["tod"].to_numpy(dtype=float)
    buyPressure = df["buyPressure"].to_numpy(dtype=float)
    rsi5 = df["rsi5"].to_numpy(dtype=float)
    rsi = df["rsi"].to_numpy(dtype=float)
    with np.errstate(invalid="ignore"):
        return (heat <= -30) & (tod >= 950) & (tod < 1100) & (buyPressure < -0.15) & (rsi5 > 70)
