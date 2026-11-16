# WORKBENCH VARIANT RW1-gapdn-bounce-flowsell-short-FD-WB3 (research only, not enabled in any account)
# parent: RW1-gapdn-bounce-flowsell-short-FD (research/bdi/fullday/RW1-gapdn-bounce-flowsell-short-FD.py); combo copy (Mechanic D8): window [950, 1500] -> [950, 1300] + RSI(14) 55-60 + 1R >= 0.40% of price + SPY-since-09:50 gate 0.20%; module clauses set by hand; 2026-11-16
# Next: backtest under docs/RESEARCH_RULES.md; testing arena only with the owner's yes. Educational only - not financial advice.
"""RW1-gapdn-bounce-flowsell-short-FD - FULL-DAY version of RW1-gapdn-bounce-flowsell-short (owner decision 2026-10-09: full-day versions
first, then identify time frames that may be better; Testing account).
Source module: research/bdi/rework1008/modules/RW1-gapdn-bounce-flowsell-short.py (copied; logic identical except the removed clause).
Removed: `(tod >= 950) & (tod <= 1100)` - the clause that limited WHEN the rule may fire (source module window 950-1100
ET bar close; source YAML window [950, 1100]).
Kept: every other condition, side, exit geometry and LAYERS (time layer replaced by the full-day note).
Run with min_adv 95000000 and window [950, 1500] (bar close ET).
Check: research/bdi/fullday/verify.json (this mask AND the source window == the source mask, open history).
Source docstring (provenance only - its results describe the WINDOWED rule, not this one):
    RW1-gapdn-bounce-flowsell-short - BDI rule-18 rework 2026-10-08 (research/bdi/rework1008). gap-down name bouncing to RSI 55-65 while heavy net selling persists.
    Lineage: MF2 (MF-open-rsimidhi-flowsell). Side short, exit t1s1 (R = 0.25 x daily ATR, exit by 15:55). Indicators on 5-minute bars.
    Source ran with min_adv 95000000 and window [950, 1100] (bar close ET).
    Lab (train 06-30..08-25 / valid 08-26..09-15, production haircut): train +0.186R t 2.47 n 323;
    valid +0.171R t 2.45 n 132. NOT scored on the locked holdouts. Research finalist only, not live.
    Educational only - not financial advice.
Educational only - not financial advice."""
import numpy as np
import pandas as pd

SIDE = "short"
GEOM = "t1s1"
SPY_MAX_SINCE_0950 = 0.2   # percent (Workbench WB3)
MIN_R_PCT = 0.40          # 1R = 0.25 x daily ATR >= 0.40% of price (Workbench WB3)
LAYERS = [
    "MarcoFlow heat <= -20 (bearish)",
    "buyPressure < -0.35 (heavy net selling, 19 bars)",
    "55 <= RSI(14) <= 60 (Workbench WB3; parent 55-65)",
    "1R (0.25 x daily ATR) >= 0.40% of price (Workbench WB3)",
    "skip when SPY is up more than +0.20% since the 09:50 bar close (needs context: [spy_fo]) (Workbench WB3)",
    "gapped down at the open",
    "bar close 09:50-13:00 ET (YAML window [950, 1300]) (Workbench WB3)",
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

    def prev(x):
        p = np.r_[np.nan, x[:-1]]
        if "symbol" in df and "date" in df:     # offline frames hold many symbol-days: no carry-over
            key = df["symbol"].astype(str).to_numpy() + "|" + df["date"].astype(str).to_numpy()
            p[np.r_[True, key[1:] != key[:-1]]] = np.nan
        return p

    rsi = col('rsi')
    gap = col('gap')
    heat = col('heat')
    bp = col('buyPressure')
    tod = col('tod')
    with np.errstate(invalid="ignore"):
        base = (heat <= -20) & (bp < -0.35) & ((rsi >= 55) & (rsi <= 60)) & (gap < 0)
        base = base & (0.25 * col('atr_d') / col('close') * 100 >= MIN_R_PCT)       # WB3: 1R >= 0.40% of price
    if "spy_fo" not in df.columns:                  # fail safe: no market context, no signal
        return np.zeros(len(df), bool)
    x = pd.DataFrame({"tod": tod, "seg": seg_key(df)})
    fo = df["spy_fo"].to_numpy(float)
    fo950 = pd.Series(np.where(tod == 950, fo, np.nan)).groupby(x.seg.values).transform("first").to_numpy(float)
    since = ((1 + fo / 100) / (1 + fo950 / 100) - 1) * 100   # SPY % change since the 09:50 bar close (owner rule: after 09:50)
    with np.errstate(invalid="ignore"):
        base = base & (since <= SPY_MAX_SINCE_0950)          # NaN (no 09:50 row) -> False
    return base
