"""MF-open-rsimidlo-flowalign - MarcoFlow rule stack 'slot-open+rsi-mid-low+flow-aligned' re-scored on the setup lab (short, t1s05).
Source: MarcoFlow StrategyReview recommendations (best Wilson LB 66, 67 signals, signal-level only).
Lab (1c/side): train exp_r +0.0186R (n 459, day-t 0.25), valid exp_r +0.0956R (n 125, day-t 1.61),
valid at production cost (+1bps/side, +2c stops, no extended-tier surcharge) +0.0590R.
Research finalist only: NOT live until the lead's locked-holdout scoring and the backlog/ledger process.
Educational only - not financial advice."""
import numpy as np

SIDE = "short"
GEOM = "t1s05"
LAYERS = [
    "heat <= -30 (a MarcoFlow bearish heat signal; direction = sign of heat)",
    "bar close 09:50-10:55 ET (MarcoFlow slot-open 9:30-11, lab starts 09:50)",
    "45 <= RSI(14) < 55 (MarcoFlow rsi-mid-low)",
    "buyPressure < -0.15 (MarcoFlow flow-aligned, short)",
]


def mask(df) -> np.ndarray:
    heat = df["heat"].to_numpy(dtype=float)
    tod = df["tod"].to_numpy(dtype=float)
    buyPressure = df["buyPressure"].to_numpy(dtype=float)
    rsi = df["rsi"].to_numpy(dtype=float)
    with np.errstate(invalid="ignore"):
        return (heat <= -30) & (tod >= 950) & (tod < 1100) & (rsi >= 45) & (rsi < 55) & (buyPressure < -0.15)
