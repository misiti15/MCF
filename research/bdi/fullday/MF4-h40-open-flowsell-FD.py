"""MF4-h40-open-flowsell-FD - FULL-DAY version of MF4-h40-open-flowsell (owner decision 2026-10-09: full-day versions
first, then identify time frames that may be better; Testing account).
Source module: research/primitives/marcoflow/MF-h40-open-flowsell.py (copied; logic identical except the removed clause).
Removed: `(tod >= 950) & (tod < 1100)` - the clause that limited WHEN the rule may fire (source module window 950-1100
ET bar close; source YAML window [950, 1100]).
Kept: every other condition, side, exit geometry and LAYERS (time layer replaced by the full-day note).
Run with min_adv 95000000 and window [950, 1500] (bar close ET).
Check: research/bdi/fullday/verify.json (this mask AND the source window == the source mask, open history).
Source docstring (provenance only - its results describe the WINDOWED rule, not this one):
    MF-h40-open-flowsell - MarcoFlow rule stack 'heat-40+slot-open+flow-sell' re-scored on the setup lab (short, t05s1).
    Source: MarcoFlow StrategyReview recommendations (best Wilson LB 64.3, 56 signals, signal-level only).
    Lab (1c/side): train exp_r +0.0238R (n 568, day-t 0.51), valid exp_r +0.1407R (n 115, day-t 3.03),
    valid at production cost (+1bps/side, +2c stops, no extended-tier surcharge) +0.1005R.
    Research finalist only: NOT live until the lead's locked-holdout scoring and the backlog/ledger process.
    Educational only - not financial advice.
Educational only - not financial advice."""
import numpy as np

SIDE = "short"
GEOM = "t05s1"
LAYERS = [
    "heat <= -30 (a MarcoFlow bearish heat signal; direction = sign of heat)",
    "|heat| >= 40 (MarcoFlow heat-40)",
    "buyPressure < -0.25 (signed volume, 19 bars; MarcoFlow flow-sell)",
    "full day: bar close 09:50-15:00 ET (YAML window [950, 1500])",
]


def mask(df) -> np.ndarray:
    heat = df["heat"].to_numpy(dtype=float)
    tod = df["tod"].to_numpy(dtype=float)
    buyPressure = df["buyPressure"].to_numpy(dtype=float)
    with np.errstate(invalid="ignore"):
        return (heat <= -30) & (np.abs(heat) >= 40) & (buyPressure < -0.25)
