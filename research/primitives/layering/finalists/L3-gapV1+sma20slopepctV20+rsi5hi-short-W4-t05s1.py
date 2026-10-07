"""L3-gapV1+sma20slopepctV20+rsi5hi-short-W4-t05s1 - layered setup (layering stage, research/primitives/layering).
Side short, exit t05s1. Lab (1c/side): train exp_r +0.2439R (n 402, day-t 4.08), valid exp_r +0.2760R (n 41, day-t 5.53),
valid at approx production cost +0.2622R.
Research finalist only: NOT live until the lead's locked-holdout scoring and the backlog/ledger process.
Educational only - not financial advice."""
import numpy as np

SIDE = "short"
GEOM = "t05s1"
LAYERS = [
    "gap <= -2.657 (V1)",
    "0.5965 < sma20_slope_pct (V20)",
    "RSI(5) > 70",
    "time window: bar close 1300 <= tod < 1430 ET"
]


def mask(df) -> np.ndarray:
    def c(k):
        return df[k].to_numpy(dtype=float)

    with np.errstate(invalid="ignore"):
        return (((c('gap') <= -2.6573517322540283))
                & ((c('sma20_slope_pct') > 0.5964763522148127))
                & ((c('rsi5') > 70))
                & ((c('tod') >= 1300) & (c('tod') < 1430)))
