"""P1-dist_lod_atr_V20-short-W4-t1s1 - Layer-1 primitive (single metric) from research/primitives/primitives/scan.py.
dist_lod_atr > 0.976495  [V20 band at train quantiles], 13:00-14:30 ET, short, exit t1s1.
Train exp_r +0.0163R (n 4274), valid exp_r +0.0784R (n 1601, day-clustered t 2.33).
Research finalist only: NOT live until the lead's locked-holdout scoring and the backlog/ledger process.
Educational only - not financial advice."""
import numpy as np

SIDE = "short"
GEOM = "t1s1"
LAYERS = [
    "dist_lod_atr > 0.976495 (V20 band of dist_lod_atr at train quantiles)",
    "time window 13:00-14:30 ET (bar close tod 1300 <= tod < 1430)",
]


def _rangepos(df):
    h = df["dist_hod_atr"].to_numpy(dtype=float)
    lo = df["dist_lod_atr"].to_numpy(dtype=float)
    s = h + lo
    with np.errstate(invalid="ignore", divide="ignore"):
        return np.where(s > 0, lo / s, np.nan)


def mask(df) -> np.ndarray:
    x = df['dist_lod_atr'].to_numpy(dtype=float)
    tod = df["tod"].to_numpy(dtype=float)
    with np.errstate(invalid="ignore"):
        return (x > 0.976495325565338) & (tod >= 1300) & (tod < 1430)
