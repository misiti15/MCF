"""L3-fromOpenD9+gapV1+rsiob-short-W4-t1s1 - layered setup (layering stage, research/primitives/layering).
Side short, exit t1s1. Lab (1c/side): train exp_r +0.2733R (n 194, day-t 3.03), valid exp_r +0.3822R (n 97, day-t 3.13),
valid at approx production cost +0.3618R.
Research finalist only: NOT live until the lead's locked-holdout scoring and the backlog/ledger process.
Educational only - not financial advice."""
import numpy as np

SIDE = "short"
GEOM = "t1s1"
LAYERS = [
    "1.297 < fromOpen <= 2.302 (D9)",
    "gap <= -2.657 (V1)",
    "RSI(14) > 65",
    "time window: bar close 1300 <= tod < 1430 ET"
]


def mask(df) -> np.ndarray:
    def c(k):
        return df[k].to_numpy(dtype=float)

    with np.errstate(invalid="ignore"):
        return (((c('fromOpen') > 1.2965964078903198) & (c('fromOpen') <= 2.301736593246459))
                & ((c('gap') <= -2.6573517322540283))
                & ((c('rsi') > 65))
                & ((c('tod') >= 1300) & (c('tod') < 1430)))
