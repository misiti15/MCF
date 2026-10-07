"""P1-gap_V1-short-W4-t1s05 - Layer-1 primitive (single metric) from research/primitives/primitives/scan.py.
gap <= -2.65735  [V1 band at train quantiles], 13:00-14:30 ET, short, exit t1s05.
Train exp_r +0.0642R (n 2447), valid exp_r +0.1690R (n 751, day-clustered t 2.42).
Research finalist only: NOT live until the lead's locked-holdout scoring and the backlog/ledger process.
Educational only - not financial advice."""
import numpy as np

SIDE = "short"
GEOM = "t1s05"
LAYERS = [
    "gap <= -2.65735 (V1 band of gap at train quantiles)",
    "time window 13:00-14:30 ET (bar close tod 1300 <= tod < 1430)",
]


def _rangepos(df):
    h = df["dist_hod_atr"].to_numpy(dtype=float)
    lo = df["dist_lod_atr"].to_numpy(dtype=float)
    s = h + lo
    with np.errstate(invalid="ignore", divide="ignore"):
        return np.where(s > 0, lo / s, np.nan)


def mask(df) -> np.ndarray:
    x = df['gap'].to_numpy(dtype=float)
    tod = df["tod"].to_numpy(dtype=float)
    with np.errstate(invalid="ignore"):
        return (x <= -2.6573517322540283) & (tod >= 1300) & (tod < 1430)
