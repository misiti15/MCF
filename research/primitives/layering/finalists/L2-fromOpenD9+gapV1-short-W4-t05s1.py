"""L2-fromOpenD9+gapV1-short-W4-t05s1 - layered setup (layering stage, research/primitives/layering).
Side short, exit t05s1. Lab (1c/side): train exp_r +0.1370R (n 463, day-t 2.91), valid exp_r +0.1785R (n 198, day-t 2.7),
valid at approx production cost +0.1596R.
Research finalist only: NOT live until the lead's locked-holdout scoring and the backlog/ledger process.
Educational only - not financial advice."""
import numpy as np

SIDE = "short"
GEOM = "t05s1"
LAYERS = [
    "1.297 < fromOpen <= 2.302 (D9)",
    "gap <= -2.657 (V1)",
    "time window: bar close 1300 <= tod < 1430 ET"
]


def mask(df) -> np.ndarray:
    def c(k):
        return df[k].to_numpy(dtype=float)

    with np.errstate(invalid="ignore"):
        return (((c('fromOpen') > 1.2965964078903198) & (c('fromOpen') <= 2.301736593246459))
                & ((c('gap') <= -2.6573517322540283))
                & ((c('tod') >= 1300) & (c('tod') < 1430)))
