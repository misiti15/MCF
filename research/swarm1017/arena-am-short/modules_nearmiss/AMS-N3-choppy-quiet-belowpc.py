"""AMS-N3-choppy-quiet-belowpc - arena combination (mcf/research/arena, swarm 2026-10-17).
    NEAR-MISS, NOT A CANDIDATE: fails the try-count t-bar (4.62) and the +/-10-percentile stability check.
    Written only so the backlog can forward-test it. See ../NOTES.md.
Indicators are recomputed by mcf.research.arena.indicators.compute on the frame passed in (bar closes 09:50-15:00).
Live notes: all indicators are computable from the live LabStrategy frame.
Research candidate only: NOT live until the lead's locked-holdout scoring and the backlog/ledger process.
Educational only - not financial advice."""
import numpy as np

from mcf.research.arena.indicators import compute

SIDE = 'short'
GEOM = 't05s1'
WINDOW = (1000, 1100)
CONDS = [
    ('rv12', '>=', 0.6005),
    ('day_vs_prev_range', '<=', 0.4091),
    ('from_pc_atr', '<=', -0.3489),
]
LAYERS = ['rv12 >= 0.6005 (std of 5-min returns over 12 bars (%))', "day_vs_prev_range <= 0.4091 (today's range so far / prior day's range)", 'from_pc_atr <= -0.3489 (close - prior close in daily ATRs)', 'window: bar close 1000 <= tod < 1100 ET (hi >= 1500 includes 15:00) (YAML window [1000, 1100])']


def mask(df) -> np.ndarray:
    x = compute(df, names=['day_vs_prev_range', 'from_pc_atr', 'rv12'], context=False)
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
