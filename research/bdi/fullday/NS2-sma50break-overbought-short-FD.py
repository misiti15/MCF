"""NS2-sma50break-overbought-short-FD - FULL-DAY version of NS2-sma50break-overbought-short (owner decision 2026-10-09: full-day versions
first, then identify time frames that may be better; Testing account).
Source module: research/owner1008/NS2-sma50break-overbought-short.py (copied; logic identical except the removed clause).
Removed: `(tod >= 950) & (tod <= 1130)` - the clause that limited WHEN the rule may fire (source module window 950-1130
ET bar close; source YAML window [950, 1130]).
Kept: every other condition, side, exit geometry and LAYERS (time layer replaced by the full-day note).
Run with min_adv 95000000 and window [950, 1500] (bar close ET).
Check: research/bdi/fullday/verify.json (this mask AND the source window == the source mask, open history).
Source docstring (provenance only - its results describe the WINDOWED rule, not this one):
    NS2-sma50break-overbought-short - owner-directed setup 2026-10-08 from the 'obvious metrics before big moves' scan (research/owner1008).
    Side short, exit t1s1 (R = 0.25 x daily ATR, exit by 15:55). Indicators on 5-minute bars.
    Train/valid only (scan.csv); PROBATION in the primary account at the owner's request. Educational only - not financial advice.
Educational only - not financial advice."""
import numpy as np

SIDE = "short"
GEOM = "t1s1"
LAYERS = [
    "price crosses ABOVE the 5-min 50-bar average on this bar",
    "RSI(14) >= 60",
    "stock up > 2% from the open",
    "full day: bar close 09:50-15:00 ET (YAML window [950, 1500])",
]


def mask(df) -> np.ndarray:
    def col(k):
        return df[k].to_numpy(dtype=float)

    def prev(k):
        x = col(k)
        p = np.r_[np.nan, x[:-1]]
        if "symbol" in df and "date" in df:     # offline frames hold many symbol-days: no carry-over
            key = df["symbol"].astype(str).to_numpy() + "|" + df["date"].astype(str).to_numpy()
            p[np.r_[True, key[1:] != key[:-1]]] = np.nan
        return p

    rsi, rsi5, fromOpen = col("rsi"), col("rsi5"), col("fromOpen")
    sma50, vwap, tod = col("sma50_dist_pct"), col("vwapDistPct"), col("tod")
    with np.errstate(invalid="ignore"):
        return (sma50 > 0) & (prev('sma50_dist_pct') <= 0) & (rsi >= 60) & (fromOpen > 2)
