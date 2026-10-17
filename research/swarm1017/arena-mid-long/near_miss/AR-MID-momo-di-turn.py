"""AR-MID-momo-di-turn - arena combination (mcf/research/arena, swarm 2026-10-17).
    NEAR-MISS, NOT A CANDIDATE (train t 1.70 vs bar 4.74; n_train 161 < 200). MarcoFlow momentum <= -0.65 while +DI(7) - -DI(7) >= 23
    (fresh up-turn after a decline) and rv12 >= 0.22%, 11:00-14:00, t1s1. train +0.137R, valid +0.130R; 0.9 trades/day; momentum neighbour (-0.42) is train-negative.
Indicators are recomputed by mcf.research.arena.indicators.compute on the frame passed in (bar closes 09:50-15:00).
Live notes: all indicators are computable from the live LabStrategy frame.
Research candidate only: NOT live until the lead's locked-holdout scoring and the backlog/ledger process.
Educational only - not financial advice."""
import numpy as np

from mcf.research.arena.indicators import compute

SIDE = 'long'
GEOM = 't1s1'
WINDOW = (1100, 1400)
CONDS = [
    ('momentum', '<=', -0.6468),
    ('di_diff7', '>=', 22.9449),
    ('rv12', '>=', 0.2239),
]
LAYERS = ['momentum <= -0.6468 (MarcoFlow momentum (frame column))', 'di_diff7 >= 22.9449 (+DI(7) - -DI(7), in-day)', 'rv12 >= 0.2239 (std of 5-min returns over 12 bars (%))', 'window: bar close 1100 <= tod < 1400 ET (hi >= 1500 includes 15:00) (YAML window [1100, 1400])']


def mask(df) -> np.ndarray:
    x = compute(df, names=['di_diff7', 'momentum', 'rv12'], context=False)
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
