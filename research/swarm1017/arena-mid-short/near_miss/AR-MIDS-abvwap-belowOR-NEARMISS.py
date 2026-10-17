"""AR-MIDS-abvwap-belowOR-NEARMISS - arena combination (mcf/research/arena, swarm 2026-10-17).
    NEAR-MISS, NOT A CANDIDATE: fails the t-bar (train t << 4.81); up-regime exp ~0; neighbours fail the regime gate (spike, not plateau). VALID used in the plateau check, so it is no longer clean.
Indicators are recomputed by mcf.research.arena.indicators.compute on the frame passed in (bar closes 09:50-15:00).
Live notes: all indicators are computable from the live LabStrategy frame.
Research candidate only: NOT live until the lead's locked-holdout scoring and the backlog/ledger process.
Educational only - not financial advice."""
import numpy as np

from mcf.research.arena.indicators import compute

SIDE = 'short'
GEOM = 't1s1'
WINDOW = (1100, 1230)
CONDS = [
    ('vwap_atr', '>=', 0.3364),
    ('or_high_dist_atr', '<=', -0.5399),
    ('emaDiff', '>=', 0.1422),
]
LAYERS = ['vwap_atr >= 0.3364 (close - session VWAP in daily ATRs)', 'or_high_dist_atr <= -0.5399 (close - opening-range high (09:30-09:50) in daily ATRs)', 'emaDiff >= 0.1422 (EMA9 vs EMA21 % (frame column))', 'window: bar close 1100 <= tod < 1230 ET (hi >= 1500 includes 15:00) (YAML window [1100, 1230])']


def mask(df) -> np.ndarray:
    x = compute(df, names=['emaDiff', 'or_high_dist_atr', 'vwap_atr'], context=False)
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
