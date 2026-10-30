"""Testing 2, OWNER EXCEPTION PDL-1a (owner 2026-10-30 ~08:00 ET, 'Move forward with 1a'): Failed Prior-Day-Low Break,
SPY-range regime, SHORT leg. Educational only - not financial advice.

NOT A CANDIDATE - a forward observation below the BAR90 Testing bar (regime-day R2A: TRAIN +0.0031 / VALID +0.0071 avg R,
t 1.14 vs bar 4.355, 76.5% months positive, 54.3 trades/session, 152 configurations tried, lineage N 121,611).
Source: research/bdi/pdl1030/regime-day (row R2A). Rules and parity: pdl1a_lib.py, research/bdi/pdl1030/pdl1a/.
Signal = CWT14-failbrk-pdl-p05 first bar per symbol-day (09:50-15:00) with cost <= 5% of R1 (0.25 ATR); taken
SHORT (same signal-bar close, mirrored exits) on days SPY's prior-day range / ATR < 0.7956 (the long leg takes the other days).
Exit: GEOM "S" - stop 0.75 ATR, target 0.125 ATR (the parent's +0.5R price), half off at 0.0625 ATR then breakeven
(YAML scale_out_r 1/12 + live_scale_out), flat 15:55. Needs YAML context: [spy_prng].
"""
import pdl1a_lib as P

SIDE = "short"
GEOM = "S"
LAYERS = ["pdl1030-regime-day-R2A-short: CWT14 p05 first bar + cost5 + S3 + SPY prior-range regime"]


def mask(df):
    return P.mask(df, SIDE)


def stop_price(f, i):
    return P.stop_price(f, i, SIDE)


def target_price(f, i, stop):
    return P.target_price(f, i, SIDE)
