"""RW1-gapdn-bounce-flowsell-short - BDI rule-18 rework 2026-10-08 (research/bdi/rework1008). gap-down name bouncing to RSI 55-65 while heavy net selling persists.
Lineage: MF2 (MF-open-rsimidhi-flowsell). Side short, exit t1s1 (R = 0.25 x daily ATR, exit by 15:55). Indicators on 5-minute bars.
Run with min_adv 95000000 and window [950, 1100] (bar close ET).
Lab (train 06-30..08-25 / valid 08-26..09-15, production haircut): train +0.186R t 2.47 n 323;
valid +0.171R t 2.45 n 132. NOT scored on the locked holdouts. Research finalist only, not live.
Educational only - not financial advice."""
import numpy as np

SIDE = "short"
GEOM = "t1s1"
LAYERS = ['MarcoFlow heat <= -20 (bearish)', 'buyPressure < -0.35 (heavy net selling, 19 bars)', '55 <= RSI(14) <= 65', 'gapped down at the open', '09:50-11:00 ET (bar close)']


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
        return (heat <= -20) & (bp < -0.35) & ((rsi >= 55) & (rsi <= 65)) & (gap < 0) & (tod >= 950) & (tod <= 1100)
