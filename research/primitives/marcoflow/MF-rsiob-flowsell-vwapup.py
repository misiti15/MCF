"""MF-rsiob-flowsell-vwapup - MarcoFlow rule stack 'rsi-ob+flow-sell+vwap-above' re-scored on the setup lab (short, t1s05).
Source: MarcoFlow StrategyReview recommendations (best Wilson LB 65.6, 31 signals, signal-level only).
Lab (1c/side): train exp_r +0.0036R (n 1370, day-t 0.1), valid exp_r +0.1135R (n 411, day-t 2.1),
valid at production cost (+1bps/side, +2c stops, no extended-tier surcharge) +0.0414R.
Research finalist only: NOT live until the lead's locked-holdout scoring and the backlog/ledger process.
Educational only - not financial advice."""
import numpy as np

SIDE = "short"
GEOM = "t1s05"
LAYERS = [
    "heat <= -30 (a MarcoFlow bearish heat signal; direction = sign of heat)",
    "RSI(14) > 65 (MarcoFlow rsi-ob)",
    "buyPressure < -0.25 (signed volume, 19 bars; MarcoFlow flow-sell)",
    "vwapDistPct > +0.05% (price above session VWAP; MarcoFlow vwap-above)",
    "time window 09:50-15:00 ET (lab frame)",
]


def mask(df) -> np.ndarray:
    heat = df["heat"].to_numpy(dtype=float)
    buyPressure = df["buyPressure"].to_numpy(dtype=float)
    vwapDistPct = df["vwapDistPct"].to_numpy(dtype=float)
    rsi = df["rsi"].to_numpy(dtype=float)
    with np.errstate(invalid="ignore"):
        return (heat <= -30) & (rsi > 65) & (buyPressure < -0.25) & (vwapDistPct > 0.05)
