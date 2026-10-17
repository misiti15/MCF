"""NM-PM-S-gapdn-above-pdh-rvol - arena combination (mcf/research/arena, swarm 2026-10-17).
    NEAR-MISS (not a candidate): base of the candidate family; train t 3.46 < bar 4.89.
Indicators are recomputed by mcf.research.arena.indicators.compute on the frame passed in (bar closes 09:50-15:00).
Live notes: all indicators are computable from the live LabStrategy frame.
Research candidate only: NOT live until the lead's locked-holdout scoring and the backlog/ledger process.
Educational only - not financial advice."""
import numpy as np

from mcf.research.arena.indicators import compute

SIDE = 'short'
GEOM = 't1s1'
WINDOW = (1400, 1530)
CONDS = [
    ('gap_atr', '<=', -0.6141),
    ('dist_pdh_atr', '<=', -0.1494),
    ('rvol_day', '>=', 0.8386),
]
LAYERS = ['gap_atr <= -0.6141 (open - prior close in daily ATRs)', 'dist_pdh_atr <= -0.1494 (prior-day high - close in ATRs (frame column))', 'rvol_day >= 0.8386 (mean volumeRatio since 09:50 (rvol proxy))', 'window: bar close 1400 <= tod < 1530 ET (hi >= 1500 includes 15:00) (YAML window [1400, 1500])']


def mask(df) -> np.ndarray:
    x = compute(df, names=['dist_pdh_atr', 'gap_atr', 'rvol_day'], context=False)
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
