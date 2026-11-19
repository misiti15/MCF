"""AR-ETF-late-dip-di-long - arena combination (mcf/research/arena, swarm 2026-10-17).
    Index/sector/leveraged ETFs, LONG, 14:00-15:00: a sharp 15-minute drop (ret3 <= -0.80%) while +DI(7) >= -DI(7)
    in a high-volatility ETF (daily ATR >= 3.6% of price: mostly 3x funds). Half-R target, 1R stop, flat 15:55.
    Passes the pre-declared quality gates (train +0.250R t 5.10 vs bar 5.00; valid +0.029R t 0.50) but FAILS the
    concentration diagnostic: best day = 31% of P/L, valid down-regime -0.11R, 2026Q2 -0.16R. See NOTES.md.
Indicators are recomputed by mcf.research.arena.indicators.compute on the frame passed in (bar closes 09:50-15:00).
Live notes: all indicators are computable from the live LabStrategy frame.
Research candidate only: NOT live until the lead's locked-holdout scoring and the backlog/ledger process.
Educational only - not financial advice."""
import numpy as np

from mcf.research.arena.indicators import compute

SIDE = 'long'
GEOM = 't05s1'
WINDOW = (1400, 1500)
CONDS = [
    ('ret3', '<=', -0.7977116525173187),
    ('di_diff7', '>=', 0.0),
    ('atr_d_pct', '>=', 3.5967583179473883),
]
# ETF-only setup: the history was scored on these symbols only. LabStrategy.eligible() has no symbol
# allow-list today, so live needs one (config or runner change); the mask applies it when the frame has 'symbol'.
SYMBOLS = frozenset(['ARKG', 'ARKK', 'AVUV', 'BULZ', 'CIBR', 'COPX', 'DDM', 'DIA', 'DOG', 'DPST', 'DUST', 'DXD', 'ERX', 'ERY', 'FAS', 'FAZ', 'FNGU', 'GDX', 'GDXJ', 'GDXU', 'IBB', 'ICLN', 'IGV', 'IHI', 'IJH', 'IJR', 'ITA', 'ITB', 'IVV', 'IVW', 'IWF', 'IWM', 'IWN', 'IWO', 'IWP', 'IWR', 'IYR', 'IYW', 'JETS', 'JNUG', 'KBE', 'KBWB', 'KRE', 'LABD', 'LABU', 'MAGS', 'MDY', 'MGK', 'MTUM', 'NUGT', 'OIH', 'PSQ', 'QID', 'QLD', 'QQQ', 'QQQM', 'RSP', 'RWM', 'SCHA', 'SCHG', 'SCHH', 'SDOW', 'SDS', 'SH', 'SILJ', 'SMH', 'SOXL', 'SOXQ', 'SOXS', 'SOXX', 'SPDN', 'SPLG', 'SPMD', 'SPMO', 'SPSM', 'SPXL', 'SPXS', 'SPXU', 'SPY', 'SPYG', 'SQQQ', 'SRTY', 'SSO', 'TAN', 'TECL', 'TECS', 'TNA', 'TQQQ', 'TWM', 'TZA', 'UDOW', 'UPRO', 'URA', 'URTY', 'UWM', 'VB', 'VDE', 'VFH', 'VGT', 'VLUE', 'VNQ', 'VO', 'VONG', 'VOO', 'VOOG', 'VTI', 'VTWO', 'VUG', 'XBI', 'XHB', 'XLB', 'XLC', 'XLE', 'XLF', 'XLI', 'XLK', 'XLP', 'XLRE', 'XLU', 'XLV', 'XLY', 'XME', 'XOP', 'XRT'])
LAYERS = ['ret3 <= -0.7977116525173187 (3-bar (15 min) return %)', 'di_diff7 >= 0.0 (+DI(7) - -DI(7), in-day)', 'atr_d_pct >= 3.5967583179473883 (daily ATR % of price)', 'window: bar close 1400 <= tod < 1500 ET (hi >= 1500 includes 15:00) (YAML window [1400, 1500])']


def mask(df) -> np.ndarray:
    x = compute(df, names=['atr_d_pct', 'di_diff7', 'ret3'], context=False)
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
    if "symbol" in getattr(df, "columns", ()):
        m &= df["symbol"].astype(str).isin(SYMBOLS).to_numpy()
    return np.asarray(m, dtype=bool)
