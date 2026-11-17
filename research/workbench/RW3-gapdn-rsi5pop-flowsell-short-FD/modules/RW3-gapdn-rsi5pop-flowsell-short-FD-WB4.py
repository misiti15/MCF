# WORKBENCH VARIANT RW3-gapdn-rsi5pop-flowsell-short-FD-WB4 (UPDAY SW1; owner "SPYEXIT build yes" 2026-11-16)
# parent: RW3-gapdn-rsi5pop-flowsell-short-FD; = WB3 with its SPY-up SKIP gate (SPY > +0.20% since 09:50) swapped for the
#   L3-WB5 up-day parts: no new entries after 12:00 while SPY is > +0.15% above its 09:50 close (this module; needs
#   `context: [spy_fo]`) + exit once SPY has risen +0.30% since entry (config `spy_exit_pct: 0.30`, runner/engine).
#   Window 10:30-15:00 and daily ATR >= 1.6% of price (1R >= 0.40%) kept. Evidence research/workbench/UPDAY/
#   RW3-gapdn-rsi5pop-flowsell-short-FD/RESULTS.md (SW1). Educational only - not financial advice.
"""RW3-gapdn-rsi5pop-flowsell-short-FD - FULL-DAY version of RW3-gapdn-rsi5pop-flowsell-short (owner decision 2026-10-09: full-day versions
first, then identify time frames that may be better; Testing account).
Source module: research/bdi/rework1008/modules/RW3-gapdn-rsi5pop-flowsell-short.py (copied; logic identical except the removed clause).
Removed: `(tod >= 950) & (tod <= 1100)` - the clause that limited WHEN the rule may fire (source module window 950-1100
ET bar close; source YAML window [950, 1100]).
Kept: every other condition, side, exit geometry and LAYERS (time layer replaced by the full-day note).
Run with min_adv 95000000 and window [1030, 1500] (bar close ET).
Check: research/bdi/fullday/verify.json (this mask AND the source window == the source mask, open history).
Source docstring (provenance only - its results describe the WINDOWED rule, not this one):
    RW3-gapdn-rsi5pop-flowsell-short - BDI rule-18 rework 2026-10-08 (research/bdi/rework1008). gap-down name with a sharp RSI(5) pop into heavy net selling.
    Lineage: MF3 (MF-open-flowsell-rsi5hi). Side short, exit t1s1 (R = 0.25 x daily ATR, exit by 15:55). Indicators on 5-minute bars.
    Source ran with min_adv 95000000 and window [950, 1100] (bar close ET).
    Lab (train 06-30..08-25 / valid 08-26..09-15, production haircut): train +0.124R t 1.59 n 211;
    valid +0.163R t 1.56 n 92. NOT scored on the locked holdouts. Research finalist only, not live.
    Educational only - not financial advice.
Educational only - not financial advice."""
import numpy as np

SIDE = "short"
GEOM = "t1s1"
LAYERS = [
    "MarcoFlow heat <= -20 (bearish)",
    "buyPressure < -0.35 (heavy net selling, 19 bars)",
    "RSI(5) > 80",
    "gapped down at the open",
    "full day: bar close 09:50-15:00 ET (YAML window [950, 1500])",
    "WB3: window 10:30-15:00 (YAML window [1030, 1500])",
    "WB4 up-day gate: no entries after 12:00 while SPY is > +0.15% above the 09:50 bar close",
    "WB4 exit: close once SPY is up +0.30% since entry (config spy_exit_pct: 0.30)",
    "WB3 intake: daily ATR >= 1.6% of price (1R >= 0.40% of price)",
]


UP_STATE_SINCE_0950 = 0.15  # percent: SPY up more than this since the 09:50 bar close = up state (UPDAY U15)
UP_STATE_END_TOD = 1200     # in the up state, no entries on bars closing after 12:00 ET


def _spy_since_0950(df) -> np.ndarray:
    """SPY % change since the 09:50 bar close, from the runner's `spy_fo` context column (SPY % from today's first 5-minute
    open to the close of the same bar): (1 + fo) / (1 + fo at the 09:50 bar) - 1. NaN when there is no 09:50 row."""
    import pandas as pd
    fo = df["spy_fo"].to_numpy(dtype=float)
    tod = df["tod"].to_numpy(dtype=float)
    if "date" in df:
        day = df["date"].astype(str).to_numpy()
    else:
        day = pd.DatetimeIndex(df.index).strftime("%Y-%m-%d").to_numpy()
    if "symbol" in df:
        day = df["symbol"].astype(str).to_numpy() + "|" + day
    at950 = pd.Series(np.where(tod == 950, fo, np.nan)).groupby(day).transform("first").to_numpy(dtype=float)
    return ((1 + fo / 100) / (1 + at950 / 100) - 1) * 100

MIN_ATR_PCT = 1.6   # daily ATR >= 1.6% of price, i.e. 1R (0.25 x ATR) >= 0.40% of price (cost floor)


def mask(df) -> np.ndarray:
    def col(k):
        return df[k].to_numpy(dtype=float)

    def prev(x):
        p = np.r_[np.nan, x[:-1]]
        if "symbol" in df and "date" in df:     # offline frames hold many symbol-days: no carry-over
            key = df["symbol"].astype(str).to_numpy() + "|" + df["date"].astype(str).to_numpy()
            p[np.r_[True, key[1:] != key[:-1]]] = np.nan
        return p

    rsi = col('rsi')
    rsi5 = col('rsi5')
    gap = col('gap')
    heat = col('heat')
    bp = col('buyPressure')
    tod = col('tod')
    with np.errstate(invalid="ignore"):
        m = (heat <= -20) & (bp < -0.35) & (rsi5 > 80) & (gap < 0)
    m &= (col("atr_d") / col("close") * 100 >= MIN_ATR_PCT)
    if "spy_fo" not in df.columns:          # fail safe: no market context -> no signal (needs `context: [spy_fo]`)
        return m & False
    with np.errstate(invalid="ignore"):
        up = _spy_since_0950(df) > UP_STATE_SINCE_0950          # NaN (no 09:50 row) -> not up state
    return m & ~(up & (tod > UP_STATE_END_TOD))

