"""RW7-gapdn-bounce-early-short - BDI rule-18 rework 2026-10-08 (research/bdi/rework1008). RW1 with lighter selling, 09:50-10:30 only.
Lineage: MF2. Side short, exit t1s1 (R = 0.25 x daily ATR, exit by 15:55). Indicators on 5-minute bars.
Run with min_adv 95000000 and window [950, 1030] (bar close ET).
Lab (train 06-30..08-25 / valid 08-26..09-15, production haircut): train +0.059R t 0.67 n 175;
valid +0.153R t 1.84 n 69. NOT scored on the locked holdouts. Research finalist only, not live.
Educational only - not financial advice."""
import numpy as np

SIDE = "short"
GEOM = "t1s1"
LAYERS = ['MarcoFlow heat <= -20 (bearish)', 'buyPressure < -0.15 (net selling)', '55 <= RSI(14) <= 65', 'gapped down at the open', '09:50-10:30 ET (bar close)']


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
        return (heat <= -20) & (bp < -0.15) & ((rsi >= 55) & (rsi <= 65)) & (gap < 0) & (tod >= 950) & (tod <= 1030)
