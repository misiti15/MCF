"""AR-MIDS-macdneg-abvwap-widerange-NEARMISS - arena combination (mcf/research/arena, swarm 2026-10-17).
    NEAR-MISS, NOT A CANDIDATE: fails the t-bar (train t << 4.81); up-regime exp ~0; neighbours fail the regime gate (spike, not plateau). VALID used in the plateau check, so it is no longer clean.
Indicators are recomputed by mcf.research.arena.indicators.compute on the frame passed in (bar closes 09:50-15:00).
Live notes: all indicators are computable from the live LabStrategy frame.
Research candidate only: NOT live until the lead's locked-holdout scoring and the backlog/ledger process.
Educational only - not financial advice."""
import numpy as np

from mcf.research.arena.indicators import compute

SIDE = 'short'
GEOM = 't1s05'
WINDOW = (1230, 1400)
CONDS = [
    ('macdPct', 'between', (-inf, -0.2973)),
    ('vwap_atr', '>=', 0.1627),
    ('day_range_atr', '>=', 0.9828),
]
LAYERS = ['macdPct between (-inf, -0.2973) (MACD line % of price (frame column))', 'vwap_atr >= 0.1627 (close - session VWAP in daily ATRs)', "day_range_atr >= 0.9828 (today's range so far in daily ATRs)", 'window: bar close 1230 <= tod < 1400 ET (hi >= 1500 includes 15:00) (YAML window [1230, 1400])']


def mask(df) -> np.ndarray:
    x = compute(df, names=['day_range_atr', 'macdPct', 'vwap_atr'], context=False)
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
