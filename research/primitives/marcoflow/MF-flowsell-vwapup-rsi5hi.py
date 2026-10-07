"""MF-flowsell-vwapup-rsi5hi - MarcoFlow rule stack 'flow-sell+vwap-above+rsi5-high' re-scored on the setup lab (short, t1s1).
Source: MarcoFlow StrategyReview recommendations (best Wilson LB 70, 20 signals, signal-level only).
Lab (1c/side): train exp_r +0.0146R (n 901, day-t 0.25), valid exp_r +0.2152R (n 283, day-t 2.51),
valid at production cost (+1bps/side, +2c stops, no extended-tier surcharge) +0.1569R.
Research finalist only: NOT live until the lead's locked-holdout scoring and the backlog/ledger process.
Educational only - not financial advice."""
import numpy as np

SIDE = "short"
GEOM = "t1s1"
LAYERS = [
    "heat <= -30 (a MarcoFlow bearish heat signal; direction = sign of heat)",
    "buyPressure < -0.25 (signed volume, 19 bars; MarcoFlow flow-sell)",
    "vwapDistPct > +0.05% (price above session VWAP; MarcoFlow vwap-above)",
    "RSI(5) > 70 (MarcoFlow rsi5-high)",
    "time window 09:50-15:00 ET (lab frame)",
]


def mask(df) -> np.ndarray:
    heat = df["heat"].to_numpy(dtype=float)
    buyPressure = df["buyPressure"].to_numpy(dtype=float)
    vwapDistPct = df["vwapDistPct"].to_numpy(dtype=float)
    rsi5 = df["rsi5"].to_numpy(dtype=float)
    rsi = df["rsi"].to_numpy(dtype=float)
    with np.errstate(invalid="ignore"):
        return (heat <= -30) & (buyPressure < -0.25) & (vwapDistPct > 0.05) & (rsi5 > 70)
