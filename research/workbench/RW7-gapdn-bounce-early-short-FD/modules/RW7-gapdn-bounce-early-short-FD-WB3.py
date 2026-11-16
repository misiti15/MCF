"""RW7-gapdn-bounce-early-short-FD-WB3 - Workbench copy (Mechanic 2026-11-16) of RW7-gapdn-bounce-early-short-FD: combo: SPY gates after 09:50 (since 09:50 <= +0.10%, last 30 min <= +0.20%) + gap < -0.5% + entries end 13:00.
Display name: "Gap-Down Early Bounce Short (all day) — WB3: SPY-after-09:50 gates + gap < -0.5% + end 13:00". Research only until deployed by the Workbench rules (RESULTS.md). Parent text follows.
RW7-gapdn-bounce-early-short-FD - FULL-DAY version of RW7-gapdn-bounce-early-short (owner decision 2026-10-09: full-day versions
first, then identify time frames that may be better; Testing account).
Source module: research/bdi/rework1008/modules/RW7-gapdn-bounce-early-short.py (copied; logic identical except the removed clause).
Removed: `(tod >= 950) & (tod <= 1030)` - the clause that limited WHEN the rule may fire (source module window 950-1030
ET bar close; source YAML window [950, 1030]).
Kept: every other condition, side, exit geometry and LAYERS (time layer replaced by the full-day note).
Run with min_adv 95000000 and window [950, 1500] (bar close ET).
Check: research/bdi/fullday/verify.json (this mask AND the source window == the source mask, open history).
Source docstring (provenance only - its results describe the WINDOWED rule, not this one):
    RW7-gapdn-bounce-early-short - BDI rule-18 rework 2026-10-08 (research/bdi/rework1008). RW1 with lighter selling, 09:50-10:30 only.
    Lineage: MF2. Side short, exit t1s1 (R = 0.25 x daily ATR, exit by 15:55). Indicators on 5-minute bars.
    Source ran with min_adv 95000000 and window [950, 1030] (bar close ET).
    Lab (train 06-30..08-25 / valid 08-26..09-15, production haircut): train +0.059R t 0.67 n 175;
    valid +0.153R t 1.84 n 69. NOT scored on the locked holdouts. Research finalist only, not live.
    Educational only - not financial advice.
Educational only - not financial advice."""
import numpy as np
import pandas as pd

SIDE = "short"
GEOM = "t1s1"
SPY_MAX_SINCE_0950 = 0.1   # percent; None = no gate
SPY_MAX_LAST_30MIN = 0.2   # percent; None = no gate
LAYERS = [
    "MarcoFlow heat <= -20 (bearish)",
    "buyPressure < -0.15 (net selling)",
    "55 <= RSI(14) <= 65",
    "gapped down at least 0.5% at the open (gap < -0.5%) (Workbench WB3)",
    "stop-exit round-trip cost (2 x (1c + 1 bp) + 2c) <= 0.15 of 1R (= the testing accounts' cost filter, kept in the module)",
    "skip when SPY is up more than +0.10% since the 09:50 bar close (needs context: [spy_fo]) (Workbench WB3)",
    "skip when SPY is up more than +0.20% over the last 30 minutes, reference never before the 09:50 bar close (Workbench WB3)",
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

    rsi = col('rsi')
    gap = col('gap')
    heat = col('heat')
    bp = col('buyPressure')
    tod = col('tod')
    with np.errstate(invalid="ignore"):
        base = (heat <= -20) & (bp < -0.15) & ((rsi >= 55) & (rsi <= 65)) & (gap < -0.5)
        base = base & (((2 * (0.01 + col('close') * 1e-4) + 0.02) / (0.25 * col('atr_d'))) <= 0.15)   # stop-exit cost <= 0.15R
    if SPY_MAX_SINCE_0950 is None and SPY_MAX_LAST_30MIN is None:
        return base
    if "spy_fo" not in df.columns:                  # fail safe: no market context, no signal
        return np.zeros(len(df), bool)
    seg = seg_key(df)
    fo = df["spy_fo"].to_numpy(float)
    lvl = 1 + fo / 100                               # SPY close / SPY open (the open cancels in every ratio below)
    with np.errstate(invalid="ignore"):
        if SPY_MAX_SINCE_0950 is not None:           # owner rule: market state measured after 09:50
            l950 = pd.Series(np.where(tod == 950, lvl, np.nan)).groupby(seg).transform("first").to_numpy(float)
            base = base & (((lvl / l950 - 1) * 100) <= SPY_MAX_SINCE_0950)          # NaN (no 09:50 row) -> False
        if SPY_MAX_LAST_30MIN is not None:
            mins = (tod // 100) * 60 + tod % 100
            ref_t = np.maximum(mins - 30, 9 * 60 + 50)                               # 30 min back, never before 09:50
            ref_tod = (ref_t // 60) * 100 + ref_t % 60
            key = pd.Series(seg).astype(str) + "|" + pd.Series(tod.astype(int)).astype(str)
            look = pd.Series(lvl, index=key.values)
            look = look[~look.index.duplicated()]
            ref = look.reindex((pd.Series(seg).astype(str) + "|" + pd.Series(ref_tod.astype(int)).astype(str)).values).to_numpy(float)
            base = base & (((lvl / ref - 1) * 100) <= SPY_MAX_LAST_30MIN)            # NaN -> False
    return base
