"""AR-MID-gapup-pullback-pdh - arena combination (mcf/research/arena, swarm 2026-10-17).
    NEAR-MISS, NOT A CANDIDATE (fails the try-count t-bar: train t 0.95 vs 4.74). Gap-up (>= 0.25 ATR) name whose MACD is
    deeply negative (<= -0.48% of price) while it still trades within 0.38 ATR below / above the prior-day high, 12:30-14:00, t05s1.
    train +0.060R n 636, valid +0.054R n 555; down-regime +0.001R; best day 2025-04-14 = 41% of P/L; neighbours fragile.
Indicators are recomputed by mcf.research.arena.indicators.compute on the frame passed in (bar closes 09:50-15:00).
Live notes: all indicators are computable from the live LabStrategy frame.
Research candidate only: NOT live until the lead's locked-holdout scoring and the backlog/ledger process.
Educational only - not financial advice."""
import numpy as np

from mcf.research.arena.indicators import compute

SIDE = 'long'
GEOM = 't05s1'
WINDOW = (1230, 1400)
CONDS = [
    ('macdPct', '<=', -0.4763),
    ('dist_pdh_atr', '<=', 0.3806),
    ('gap_atr', '>=', 0.2464),
]
LAYERS = ['macdPct <= -0.4763 (MACD line % of price (frame column))', 'dist_pdh_atr <= 0.3806 (prior-day high - close in ATRs (frame column))', 'gap_atr >= 0.2464 (open - prior close in daily ATRs)', 'window: bar close 1230 <= tod < 1400 ET (hi >= 1500 includes 15:00) (YAML window [1230, 1400])']


def mask(df) -> np.ndarray:
    x = compute(df, names=['dist_pdh_atr', 'gap_atr', 'macdPct'], context=False)
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
