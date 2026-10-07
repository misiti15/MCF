"""P1-rsi_D7-short-W1-t1s1 - Layer-1 primitive (single metric) from research/primitives/primitives/scan.py.
54.7134 < rsi <= 59.6154  [D7 band at train quantiles], 09:50-10:30 ET, short, exit t1s1.
Train exp_r +0.0173R (n 14061), valid exp_r +0.0684R (n 4645, day-clustered t 1.82).
Research finalist only: NOT live until the lead's locked-holdout scoring and the backlog/ledger process.
Educational only - not financial advice."""
import numpy as np

SIDE = "short"
GEOM = "t1s1"
LAYERS = [
    "54.7134 < rsi <= 59.6154 (D7 band of rsi at train quantiles)",
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
        return (x > 54.71342468261719) & (x <= 59.61538314819336) & (tod >= 950) & (tod < 1030)
