"""MF-open-rsimidlo-flowsell - MarcoFlow rule stack 'open-after10+rsi-mid-low+flow-sell' re-scored on the setup lab (short, t1s05).
Source: MarcoFlow StrategyReview recommendations (best Wilson LB 65.6, 23 signals, signal-level only).
Lab (1c/side): train exp_r +0.0244R (n 338, day-t 0.33), valid exp_r +0.1021R (n 91, day-t 1.54),
valid at production cost (+1bps/side, +2c stops, no extended-tier surcharge) +0.0661R.
Research finalist only: NOT live until the lead's locked-holdout scoring and the backlog/ledger process.
Educational only - not financial advice."""
import numpy as np

SIDE = "short"
GEOM = "t1s05"
LAYERS = [
    "heat <= -30 (a MarcoFlow bearish heat signal; direction = sign of heat)",
    "bar close 09:50-10:55 ET (MarcoFlow open-after10)",
    "45 <= RSI(14) < 55 (MarcoFlow rsi-mid-low)",
    "buyPressure < -0.25 (signed volume, 19 bars; MarcoFlow flow-sell)",
]


def mask(df) -> np.ndarray:
    heat = df["heat"].to_numpy(dtype=float)
    tod = df["tod"].to_numpy(dtype=float)
    buyPressure = df["buyPressure"].to_numpy(dtype=float)
    rsi = df["rsi"].to_numpy(dtype=float)
    with np.errstate(invalid="ignore"):
        return (heat <= -30) & (tod >= 950) & (tod < 1100) & (rsi >= 45) & (rsi < 55) & (buyPressure < -0.25)
