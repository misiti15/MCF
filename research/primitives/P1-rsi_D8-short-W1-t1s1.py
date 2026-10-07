"""P1-rsi_D8-short-W1-t1s1 - Layer-1 primitive (single metric) from research/primitives/primitives/scan.py.
59.6154 < rsi <= 65.3232  [D8 band at train quantiles], 09:50-10:30 ET, short, exit t1s1.
Train exp_r +0.0105R (n 14519), valid exp_r +0.0988R (n 4379, day-clustered t 1.94).
Research finalist only: NOT live until the lead's locked-holdout scoring and the backlog/ledger process.
Educational only - not financial advice."""
import numpy as np

SIDE = "short"
GEOM = "t1s1"
LAYERS = [
    "59.6154 < rsi <= 65.3232 (D8 band of rsi at train quantiles)",
    "time window 09:50-10:30 ET (bar close tod 950 <= tod < 1030)",
]


def _rangepos(df):
    h = df["dist_hod_atr"].to_numpy(dtype=float)
    lo = df["dist_lod_atr"].to_numpy(dtype=float)
    s = h + lo
    with np.errstate(invalid="ignore", divide="ignore"):
        return np.where(s > 0, lo / s, np.nan)


def mask(df) -> np.ndarray:
    x = df['rsi'].to_numpy(dtype=float)
    tod = df["tod"].to_numpy(dtype=float)
    with np.errstate(invalid="ignore"):
        return (x > 59.61538314819336) & (x <= 65.32317504882813) & (tod >= 950) & (tod < 1030)
