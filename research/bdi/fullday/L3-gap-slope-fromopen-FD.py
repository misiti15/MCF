"""L3-gap-slope-fromopen-FD - FULL-DAY version of L3-gap-slope-fromopen (owner decision 2026-10-09: full-day versions
first, then identify time frames that may be better; Testing account).
Source module: research/primitives/layering/finalists/L3-gapV1+sma20slopepctD10+fromOpenV20-short-W4-t1s1.py (copied; logic identical except the removed clause).
Removed: `(c('tod') >= 1300) & (c('tod') < 1430)` - the clause that limited WHEN the rule may fire (source module window 1300-1430
ET bar close; source YAML window [1300, 1430]).
Kept: every other condition, side, exit geometry and LAYERS (time layer replaced by the full-day note).
Run with min_adv 0 and window [950, 1500] (bar close ET), prefilter 'gap_le:-2.6573517322540283' (as the source).
Check: research/bdi/fullday/verify.json (this mask AND the source window == the source mask, open history).
Source docstring (provenance only - its results describe the WINDOWED rule, not this one):
    L3-gapV1+sma20slopepctD10+fromOpenV20-short-W4-t1s1 - layered setup (layering stage, research/primitives/layering).
    Side short, exit t1s1. Lab (1c/side): train exp_r +0.2650R (n 373, day-t 2.65), valid exp_r +0.3109R (n 60, day-t 3.34),
    valid at approx production cost +0.2919R.
    Research finalist only: NOT live until the lead's locked-holdout scoring and the backlog/ledger process.
    Educational only - not financial advice.
Educational only - not financial advice."""
import numpy as np

SIDE = "short"
GEOM = "t1s1"
LAYERS = [
    "gap <= -2.657 (V1)",
    "0.3724 < sma20_slope_pct (D10)",
    "3.46 < fromOpen (V20)",
    "full day: bar close 09:50-15:00 ET (YAML window [950, 1500])",
]


def mask(df) -> np.ndarray:
    def c(k):
        return df[k].to_numpy(dtype=float)

    with np.errstate(invalid="ignore"):
        return (((c('gap') <= -2.6573517322540283))
                & ((c('sma20_slope_pct') > 0.37244729995727527))
                & ((c('fromOpen') > 3.460294628143309)))
