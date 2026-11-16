"""RW5-heat30-flowsell-rsi5pop-gapdn-short-FD-WB2 - Workbench copy (Mechanic 2026-11-16) of RW5-heat30-flowsell-rsi5pop-gapdn-short-FD: P20/intake: stop-exit round-trip cost (2 x (1c + 1 bp) + 2c) <= 0.15 of 1R (1R = 0.25 x daily ATR).
Display name: "Gap-Down Pop Fade (all day) — WB2: stop cost <= 15% of 1R". Research only until deployed by the Workbench rules (RESULTS.md). Parent text follows.
RW5-heat30-flowsell-rsi5pop-gapdn-short-FD - FULL-DAY version of RW5-heat30-flowsell-rsi5pop-gapdn-short (owner decision 2026-10-09: full-day versions
first, then identify time frames that may be better; Testing account).
Source module: research/bdi/rework1008/modules/RW5-heat30-flowsell-rsi5pop-gapdn-short.py (copied; logic identical except the removed clause).
Removed: `(tod >= 950) & (tod <= 1100)` - the clause that limited WHEN the rule may fire (source module window 950-1100
ET bar close; source YAML window [950, 1100]).
Kept: every other condition, side, exit geometry and LAYERS (time layer replaced by the full-day note).
Run with min_adv 95000000 and window [950, 1500] (bar close ET).
Check: research/bdi/fullday/verify.json (this mask AND the source window == the source mask, open history).
Source docstring (provenance only - its results describe the WINDOWED rule, not this one):
    RW5-heat30-flowsell-rsi5pop-gapdn-short - BDI rule-18 rework 2026-10-08 (research/bdi/rework1008). bearish heat <= -30, net selling, RSI(5) pop, gap-down.
    Lineage: MF3 / MF5. Side short, exit t1s1 (R = 0.25 x daily ATR, exit by 15:55). Indicators on 5-minute bars.
    Source ran with min_adv 95000000 and window [950, 1100] (bar close ET).
    Lab (train 06-30..08-25 / valid 08-26..09-15, production haircut): train +0.102R t 1.06 n 147;
    valid +0.273R t 2.13 n 52. NOT scored on the locked holdouts. Research finalist only, not live.
    Educational only - not financial advice.
Educational only - not financial advice."""
import numpy as np
import pandas as pd

SIDE = "short"
GEOM = "t1s1"
SPY_MAX_SINCE_0950 = None   # percent; None = no gate
LAYERS = [
    "MarcoFlow heat <= -30 (bearish)",
    "buyPressure < -0.15 (net selling)",
    "RSI(5) > 80",
    "gapped down at the open",
    "stop-exit round-trip cost (2 x (1c + 1 bp) + 2c) <= 0.15 of 1R (Workbench WB2)",
    "bar close 09:50-15:00 ET (YAML window [950, 1500])",
]


def seg_key(df):
    if "symbol" in df and "date" in df:
        return (df["symbol"].astype(str) + "|" + df["date"].astype(str)).to_numpy()
    if isinstance(df.index, pd.DatetimeIndex):        # live frame: one segment per session date
        return np.asarray(df.index.date).astype(str)
    return np.zeros(len(df), int)


def mask(df) -> np.ndarray:
    def col(k):
        return df[k].to_numpy(dtype=float)

    rsi5 = col('rsi5')
    gap = col('gap')
    heat = col('heat')
    bp = col('buyPressure')
    tod = col('tod')
    with np.errstate(invalid="ignore"):
        base = (heat <= -30) & (bp < -0.15) & (rsi5 > 80) & (gap < 0)
    base = base & (((2 * (0.01 + col('close') * 1e-4) + 0.02) / (0.25 * col('atr_d'))) <= 0.15)   # WB: stop-exit cost <= 0.15R
    return base
