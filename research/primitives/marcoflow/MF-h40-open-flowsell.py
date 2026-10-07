"""MF-h40-open-flowsell - MarcoFlow rule stack 'heat-40+slot-open+flow-sell' re-scored on the setup lab (short, t05s1).
Source: MarcoFlow StrategyReview recommendations (best Wilson LB 64.3, 56 signals, signal-level only).
Lab (1c/side): train exp_r +0.0238R (n 568, day-t 0.51), valid exp_r +0.1407R (n 115, day-t 3.03),
valid at production cost (+1bps/side, +2c stops, no extended-tier surcharge) +0.1005R.
Research finalist only: NOT live until the lead's locked-holdout scoring and the backlog/ledger process.
Educational only - not financial advice."""
import numpy as np

SIDE = "short"
GEOM = "t05s1"
LAYERS = [
    "heat <= -30 (a MarcoFlow bearish heat signal; direction = sign of heat)",
    "|heat| >= 40 (MarcoFlow heat-40)",
    "bar close 09:50-10:55 ET (MarcoFlow slot-open 9:30-11, lab starts 09:50)",
    "buyPressure < -0.25 (signed volume, 19 bars; MarcoFlow flow-sell)",
]


def mask(df) -> np.ndarray:
    heat = df["heat"].to_numpy(dtype=float)
    tod = df["tod"].to_numpy(dtype=float)
    buyPressure = df["buyPressure"].to_numpy(dtype=float)
    with np.errstate(invalid="ignore"):
        return (heat <= -30) & (np.abs(heat) >= 40) & (tod >= 950) & (tod < 1100) & (buyPressure < -0.25)
