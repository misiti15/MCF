"""NM-PM-L-belowvwap-orh-retest - arena combination (mcf/research/arena, swarm 2026-10-17).
    NEAR-MISS (not a candidate): far below VWAP, near the day low, but the day low sits at/above the
    opening-range high (rally-then-full-fade); long 14:00-15:00. Train t 4.56 < bar 4.89, valid +0.046R t 0.78.
Indicators are recomputed by mcf.research.arena.indicators.compute on the frame passed in (bar closes 09:50-15:00).
Live notes: all indicators are computable from the live LabStrategy frame.
Research candidate only: NOT live until the lead's locked-holdout scoring and the backlog/ledger process.
Educational only - not financial advice."""
import numpy as np

from mcf.research.arena.indicators import compute

SIDE = 'long'
GEOM = 't1s1'
WINDOW = (1400, 1530)
CONDS = [
    ('vwapDistPct', '<=', -1.3328),
    ('or_high_dist_atr', '>=', -0.1904),
    ('day_pos', '<=', 0.1957),
]
LAYERS = ['vwapDistPct <= -1.3328 (close vs session VWAP % (frame column))', 'or_high_dist_atr >= -0.1904 (close - opening-range high (09:30-09:50) in daily ATRs)', "day_pos <= 0.1957 (position in today's range so far (0 = low, 1 = high))", 'window: bar close 1400 <= tod < 1530 ET (hi >= 1500 includes 15:00) (YAML window [1400, 1500])']


def mask(df) -> np.ndarray:
    x = compute(df, names=['day_pos', 'or_high_dist_atr', 'vwapDistPct'], context=False)
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
