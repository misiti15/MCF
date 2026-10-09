"""MF1-945-flowsell-vwapup-FD - FULL-DAY version of MF1-945-flowsell-vwapup (owner decision 2026-10-09: full-day versions
first, then identify time frames that may be better; Testing account).
Source module: research/primitives/marcoflow/MF-945-flowsell-vwapup.py (copied; logic identical except the removed clause).
Removed: `(tod >= 950) & (tod < 1030)` - the clause that limited WHEN the rule may fire (source module window 950-1030
ET bar close; source YAML window [950, 1030]).
Kept: every other condition, side, exit geometry and LAYERS (time layer replaced by the full-day note).
Run with min_adv 95000000 and window [950, 1500] (bar close ET).
Check: research/bdi/fullday/verify.json (this mask AND the source window == the source mask, open history).
Source docstring (provenance only - its results describe the WINDOWED rule, not this one):
    MF-945-flowsell-vwapup - MarcoFlow rule stack 'open-945-1030+flow-sell+vwap-above' re-scored on the setup lab (short, t1s05).
    Source: MarcoFlow StrategyReview recommendations (best Wilson LB 64.2, 22 signals, signal-level only).
    Lab (1c/side): train exp_r +0.0174R (n 376, day-t 0.26), valid exp_r +0.3109R (n 75, day-t 2.44),
    valid at production cost (+1bps/side, +2c stops, no extended-tier surcharge) +0.2317R.
    Research finalist only: NOT live until the lead's locked-holdout scoring and the backlog/ledger process.
    Educational only - not financial advice.
Educational only - not financial advice."""
import numpy as np

SIDE = "short"
GEOM = "t1s05"
LAYERS = [
    "heat <= -30 (a MarcoFlow bearish heat signal; direction = sign of heat)",
    "buyPressure < -0.25 (signed volume, 19 bars; MarcoFlow flow-sell)",
    "vwapDistPct > +0.05% (price above session VWAP; MarcoFlow vwap-above)",
    "full day: bar close 09:50-15:00 ET (YAML window [950, 1500])",
]


def mask(df) -> np.ndarray:
    heat = df["heat"].to_numpy(dtype=float)
    tod = df["tod"].to_numpy(dtype=float)
    buyPressure = df["buyPressure"].to_numpy(dtype=float)
    vwapDistPct = df["vwapDistPct"].to_numpy(dtype=float)
    with np.errstate(invalid="ignore"):
        return (heat <= -30) & (buyPressure < -0.25) & (vwapDistPct > 0.05)
