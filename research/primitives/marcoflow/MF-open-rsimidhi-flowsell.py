"""MF-open-rsimidhi-flowsell - MarcoFlow rule stack 'slot-open+rsi-mid-high+flow-sell' re-scored on the setup lab (short, t1s05).
Source: MarcoFlow StrategyReview recommendations (best Wilson LB 63.7, 26 signals, signal-level only).
Lab (1c/side): train exp_r +0.0714R (n 119, day-t 0.83), valid exp_r +0.1600R (n 38, day-t 1.68),
valid at production cost (+1bps/side, +2c stops, no extended-tier surcharge) +0.1237R.
Research finalist only: NOT live until the lead's locked-holdout scoring and the backlog/ledger process.
Educational only - not financial advice."""
import numpy as np

SIDE = "short"
GEOM = "t1s05"
LAYERS = [
    "heat <= -30 (a MarcoFlow bearish heat signal; direction = sign of heat)",
    "bar close 09:50-10:55 ET (MarcoFlow slot-open 9:30-11, lab starts 09:50)",
    "55 <= RSI(14) <= 65 (MarcoFlow rsi-mid-high)",
    "buyPressure < -0.25 (signed volume, 19 bars; MarcoFlow flow-sell)",
]


def mask(df) -> np.ndarray:
    heat = df["heat"].to_numpy(dtype=float)
    tod = df["tod"].to_numpy(dtype=float)
    buyPressure = df["buyPressure"].to_numpy(dtype=float)
    rsi = df["rsi"].to_numpy(dtype=float)
    with np.errstate(invalid="ignore"):
        return (heat <= -30) & (tod >= 950) & (tod < 1100) & (rsi >= 55) & (rsi <= 65) & (buyPressure < -0.25)
