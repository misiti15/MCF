"""exhaustion_short-FD - FULL-DAY version of exhaustion_short (owner decision 2026-10-09: full-day versions
first, then identify time frames that may be better; Testing account).
Source module: research/setups2/candidates/volume_flip_1.py (copied; logic identical except the removed clause).
Removed: `(tod >= 1300) & (tod <= 1500)` - the clause that limited WHEN the rule may fire (source module window 1300-1500
ET bar close; source YAML window [1300, 1500]).
Kept: every other condition, side, exit geometry and LAYERS (time layer replaced by the full-day note).
Run with min_adv 95000000 and window [950, 1500] (bar close ET), prefilter 'new_high_100m' (as the source).
Check: research/bdi/fullday/verify.json (this mask AND the source window == the source mask, open history).
Source docstring (provenance only - its results describe the WINDOWED rule, not this one):
    volume_flip #1 - afternoon bearish RSI divergence after an extended run (short, t1s1).
    Educational only - not financial advice.
Educational only - not financial advice."""
import numpy as np

SIDE = "short"
GEOM = "t1s1"
LAYERS = [
    "rsi5 > 90 (short-term overbought)",
    "sma20_dist_pct > 1.0 (close > 1% above 5-min SMA20)",
    "bear_div == 1 (price at 20-bar high while RSI(14) is >5 below its 20-bar max)",
    "full day: bar close 09:50-15:00 ET (YAML window [950, 1500])",
]


def mask(df) -> np.ndarray:
    rsi5 = df["rsi5"].to_numpy(dtype=float)
    sma20 = df["sma20_dist_pct"].to_numpy(dtype=float)
    div = df["bear_div"].to_numpy(dtype=float)
    tod = df["tod"].to_numpy(dtype=float)
    return (rsi5 > 90) & (sma20 > 1.0) & (div > 0)
