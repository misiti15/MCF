"""MF-short-flowsell-vwapup - MarcoFlow rule stack 'dir-short+flow-sell+vwap-above' re-scored on the setup lab (short, t1s05).
Source: MarcoFlow StrategyReview recommendations (best Wilson LB 63.9, 38 signals, signal-level only).
Lab (1c/side): train exp_r +0.0015R (n 1440, day-t 0.04), valid exp_r +0.1145R (n 432, day-t 2.13),
valid at production cost (+1bps/side, +2c stops, no extended-tier surcharge) +0.0441R.
Research finalist only: NOT live until the lead's locked-holdout scoring and the backlog/ledger process.
Educational only - not financial advice."""
import numpy as np

SIDE = "short"
GEOM = "t1s05"
LAYERS = [
    "heat <= -30 (a MarcoFlow bearish heat signal; direction = sign of heat)",
    "buyPressure < -0.25 (signed volume, 19 bars; MarcoFlow flow-sell)",
    "vwapDistPct > +0.05% (price above session VWAP; MarcoFlow vwap-above)",
    "time window 09:50-15:00 ET (lab frame)",
]


def mask(df) -> np.ndarray:
    heat = df["heat"].to_numpy(dtype=float)
    buyPressure = df["buyPressure"].to_numpy(dtype=float)
    vwapDistPct = df["vwapDistPct"].to_numpy(dtype=float)
    with np.errstate(invalid="ignore"):
        return (heat <= -30) & (buyPressure < -0.25) & (vwapDistPct > 0.05)
