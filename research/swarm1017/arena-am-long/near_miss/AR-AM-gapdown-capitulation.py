"""AR-AM-gapdown-capitulation - arena combination (mcf/research/arena, swarm 2026-10-17).
    NEAR-MISS, NOT A CANDIDATE: fails the try-count bar (train t 1.71 vs 4.62). Gap down >= 0.41 daily ATR, 60-min return <= -1.61%,
    rvol proxy <= 0.80; long t1s1. ret12 is NaN before the 10:50 bar, so entries are 10:50/10:55 only.
    Train concentrated in Apr 2025 (367 of 741 trades). For the lead locked-block test only.
Indicators are recomputed by mcf.research.arena.indicators.compute on the frame passed in (bar closes 09:50-15:00).
Live notes: all indicators are computable from the live LabStrategy frame.
Research candidate only: NOT live until the lead's locked-holdout scoring and the backlog/ledger process.
Educational only - not financial advice."""
import numpy as np

from mcf.research.arena.indicators import compute

SIDE = 'long'
GEOM = 't1s1'
WINDOW = (950, 1100)
CONDS = [
    ('ret12', '<=', -1.6145),
    ('gap_atr', '<=', -0.4056),
    ('rvol_day', '<=', 0.8),
]
LAYERS = ['ret12 <= -1.6145 (12-bar (60 min) return %)', 'gap_atr <= -0.4056 (open - prior close in daily ATRs)', 'rvol_day <= 0.8 (mean volumeRatio since 09:50 (rvol proxy))', 'window: bar close 950 <= tod < 1100 ET (hi >= 1500 includes 15:00) (YAML window [950, 1100])']


def mask(df) -> np.ndarray:
    x = compute(df, names=['gap_atr', 'ret12', 'rvol_day'], context=False)
    tod = df["tod"].to_numpy(dtype=float)
    m = (tod >= WINDOW[0]) & ((tod < WINDOW[1]) | ((WINDOW[1] >= 1500) & (tod <= 1500)))
    with np.errstate(invalid="ignore"):
        for nm, op, v in CONDS:
            a = x[nm].to_numpy(dtype=float)
            if op == "<=":
                m &= a <= v
            elif op == "<":
                m &= a < v
            elif op == ">=":
                m &= a >= v
            elif op == ">":
                m &= a > v
            elif op == "==":
                m &= a == v
            else:
                m &= (a >= v[0]) & (a < v[1])
    return np.asarray(m, dtype=bool)
