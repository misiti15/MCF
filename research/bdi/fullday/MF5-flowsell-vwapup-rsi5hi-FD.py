"""MF5-flowsell-vwapup-rsi5hi-FD - FULL-DAY version of MF5-flowsell-vwapup-rsi5hi (owner decision 2026-10-09: full-day versions
first, then identify time frames that may be better; Testing account).
Source module: research/primitives/marcoflow/MF-flowsell-vwapup-rsi5hi.py (copied; logic identical except the removed clause).
Removed: nothing (the source has no time-of-day clause; its window was already [950, 1500]) - the clause that limited WHEN the rule may fire (source module window 950-1500
ET bar close; source YAML window [950, 1500]).
Kept: every other condition, side, exit geometry and LAYERS (time layer replaced by the full-day note).
Run with min_adv 95000000 and window [950, 1500] (bar close ET).
Check: research/bdi/fullday/verify.json (this mask AND the source window == the source mask, open history).
Source docstring (provenance only - its results describe the WINDOWED rule, not this one):
    MF-flowsell-vwapup-rsi5hi - MarcoFlow rule stack 'flow-sell+vwap-above+rsi5-high' re-scored on the setup lab (short, t1s1).
    Source: MarcoFlow StrategyReview recommendations (best Wilson LB 70, 20 signals, signal-level only).
    Lab (1c/side): train exp_r +0.0146R (n 901, day-t 0.25), valid exp_r +0.2152R (n 283, day-t 2.51),
    valid at production cost (+1bps/side, +2c stops, no extended-tier surcharge) +0.1569R.
    Research finalist only: NOT live until the lead's locked-holdout scoring and the backlog/ledger process.
    Educational only - not financial advice.
Educational only - not financial advice."""
import numpy as np

SIDE = "short"
GEOM = "t1s1"
LAYERS = [
    "heat <= -30 (a MarcoFlow bearish heat signal; direction = sign of heat)",
    "buyPressure < -0.25 (signed volume, 19 bars; MarcoFlow flow-sell)",
    "vwapDistPct > +0.05% (price above session VWAP; MarcoFlow vwap-above)",
    "RSI(5) > 70 (MarcoFlow rsi5-high)",
    "full day: bar close 09:50-15:00 ET (YAML window [950, 1500])",
]


def mask(df) -> np.ndarray:
    heat = df["heat"].to_numpy(dtype=float)
    buyPressure = df["buyPressure"].to_numpy(dtype=float)
    vwapDistPct = df["vwapDistPct"].to_numpy(dtype=float)
    rsi5 = df["rsi5"].to_numpy(dtype=float)
    rsi = df["rsi"].to_numpy(dtype=float)
    with np.errstate(invalid="ignore"):
        return (heat <= -30) & (buyPressure < -0.25) & (vwapDistPct > 0.05) & (rsi5 > 70)
