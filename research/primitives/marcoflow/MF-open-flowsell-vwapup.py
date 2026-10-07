"""MF-open-flowsell-vwapup - MarcoFlow rule stack 'open-after10+flow-sell+vwap-above' re-scored on the setup lab (short, t1s05).
Source: MarcoFlow StrategyReview recommendations (best Wilson LB 60.8, 34 signals, signal-level only).
Lab (1c/side): train exp_r +0.0236R (n 882, day-t 0.51), valid exp_r +0.1875R (n 197, day-t 2.59),
valid at production cost (+1bps/side, +2c stops, no extended-tier surcharge) +0.1202R.
Research finalist only: NOT live until the lead's locked-holdout scoring and the backlog/ledger process.
Educational only - not financial advice."""
import numpy as np

SIDE = "short"
GEOM = "t1s05"
LAYERS = [
    "heat <= -30 (a MarcoFlow bearish heat signal; direction = sign of heat)",
    "bar close 09:50-10:55 ET (MarcoFlow open-after10)",
    "buyPressure < -0.25 (signed volume, 19 bars; MarcoFlow flow-sell)",
    "vwapDistPct > +0.05% (price above session VWAP; MarcoFlow vwap-above)",
]


def mask(df) -> np.ndarray:
    heat = df["heat"].to_numpy(dtype=float)
    tod = df["tod"].to_numpy(dtype=float)
    buyPressure = df["buyPressure"].to_numpy(dtype=float)
    vwapDistPct = df["vwapDistPct"].to_numpy(dtype=float)
    with np.errstate(invalid="ignore"):
        return (heat <= -30) & (tod >= 950) & (tod < 1100) & (buyPressure < -0.25) & (vwapDistPct > 0.05)
