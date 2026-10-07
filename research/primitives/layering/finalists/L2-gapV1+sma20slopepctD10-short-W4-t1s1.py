"""L2-gapV1+sma20slopepctD10-short-W4-t1s1 - layered setup (layering stage, research/primitives/layering).
Side short, exit t1s1. Lab (1c/side): train exp_r +0.2138R (n 887, day-t 2.97), valid exp_r +0.2539R (n 137, day-t 2.98),
valid at approx production cost +0.2309R.
Research finalist only: NOT live until the lead's locked-holdout scoring and the backlog/ledger process.
Educational only - not financial advice."""
import numpy as np

SIDE = "short"
GEOM = "t1s1"
LAYERS = [
    "gap <= -2.657 (V1)",
    "0.3724 < sma20_slope_pct (D10)",
    "time window: bar close 1300 <= tod < 1430 ET"
]


def mask(df) -> np.ndarray:
    def c(k):
        return df[k].to_numpy(dtype=float)

    with np.errstate(invalid="ignore"):
        return (((c('gap') <= -2.6573517322540283))
                & ((c('sma20_slope_pct') > 0.37244729995727527))
                & ((c('tod') >= 1300) & (c('tod') < 1430)))
