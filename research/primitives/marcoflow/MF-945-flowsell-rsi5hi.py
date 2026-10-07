"""MF-945-flowsell-rsi5hi - MarcoFlow rule stack 'open-945-1030+flow-sell+rsi5-high' re-scored on the setup lab (short, t05s1).
Source: MarcoFlow StrategyReview recommendations (best Wilson LB 64.9, 23 signals, signal-level only).
Lab (1c/side): train exp_r +0.0234R (n 281, day-t 0.4), valid exp_r +0.1660R (n 60, day-t 2.42),
valid at production cost (+1bps/side, +2c stops, no extended-tier surcharge) +0.1023R.
Research finalist only: NOT live until the lead's locked-holdout scoring and the backlog/ledger process.
Educational only - not financial advice."""
import numpy as np

SIDE = "short"
GEOM = "t05s1"
LAYERS = [
    "heat <= -30 (a MarcoFlow bearish heat signal; direction = sign of heat)",
    "bar close 09:50-10:25 ET (MarcoFlow open-945-1030)",
    "buyPressure < -0.25 (signed volume, 19 bars; MarcoFlow flow-sell)",
    "RSI(5) > 70 (MarcoFlow rsi5-high)",
]


def mask(df) -> np.ndarray:
    heat = df["heat"].to_numpy(dtype=float)
    tod = df["tod"].to_numpy(dtype=float)
    buyPressure = df["buyPressure"].to_numpy(dtype=float)
    rsi5 = df["rsi5"].to_numpy(dtype=float)
    rsi = df["rsi"].to_numpy(dtype=float)
    with np.errstate(invalid="ignore"):
        return (heat <= -30) & (tod >= 950) & (tod < 1030) & (buyPressure < -0.25) & (rsi5 > 70)
