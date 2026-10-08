"""RW5-heat30-flowsell-rsi5pop-gapdn-short - BDI rule-18 rework 2026-10-08 (research/bdi/rework1008). bearish heat <= -30, net selling, RSI(5) pop, gap-down.
Lineage: MF3 / MF5. Side short, exit t1s1 (R = 0.25 x daily ATR, exit by 15:55). Indicators on 5-minute bars.
Run with min_adv 95000000 and window [950, 1100] (bar close ET).
Lab (train 06-30..08-25 / valid 08-26..09-15, production haircut): train +0.102R t 1.06 n 147;
valid +0.273R t 2.13 n 52. NOT scored on the locked holdouts. Research finalist only, not live.
Educational only - not financial advice."""
import numpy as np

SIDE = "short"
GEOM = "t1s1"
LAYERS = ['MarcoFlow heat <= -30 (bearish)', 'buyPressure < -0.15 (net selling)', 'RSI(5) > 80', 'gapped down at the open', '09:50-11:00 ET (bar close)']


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
        return (heat <= -30) & (bp < -0.15) & (rsi5 > 80) & (gap < 0) & (tod >= 950) & (tod <= 1100)
