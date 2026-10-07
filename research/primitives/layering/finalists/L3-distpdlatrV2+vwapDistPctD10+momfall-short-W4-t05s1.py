"""L3-distpdlatrV2+vwapDistPctD10+momfall-short-W4-t05s1 - layered setup (layering stage, research/primitives/layering).
Side short, exit t05s1. Lab (1c/side): train exp_r +0.2236R (n 197, day-t 3.54), valid exp_r +0.3072R (n 54, day-t 6.62),
valid at approx production cost +0.2882R.
Research finalist only: NOT live until the lead's locked-holdout scoring and the backlog/ledger process.
Educational only - not financial advice."""
import numpy as np

SIDE = "short"
GEOM = "t05s1"
LAYERS = [
    "-0.6065 < dist_pdl_atr <= -0.3591 (V2)",
    "0.893 < vwapDistPct (D10)",
    "RSI(14) 3-bar slope < -1",
    "time window: bar close 1300 <= tod < 1430 ET"
]


def mask(df) -> np.ndarray:
    def c(k):
        return df[k].to_numpy(dtype=float)

    with np.errstate(invalid="ignore"):
        return (((c('dist_pdl_atr') > -0.6065093755722046) & (c('dist_pdl_atr') <= -0.3591294586658478))
                & ((c('vwapDistPct') > 0.8929907679557797))
                & ((c('rsiSlope') < -1.0))
                & ((c('tod') >= 1300) & (c('tod') < 1430)))
