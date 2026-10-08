"""RW8-sma50up-spikefade-short - BDI rule-18 rework 2026-10-08 (research/bdi/rework1008). close crosses above SMA50 on a >3% up day while RSI(14) <= 30.
Lineage: NS2 (scan neighbour). Side short, exit t1s1 (R = 0.25 x daily ATR, exit by 15:55). Indicators on 5-minute bars.
Run with min_adv 95000000 and window [950, 1500] (bar close ET).
Lab (train 06-30..08-25 / valid 08-26..09-15, production haircut): train +0.026R t 0.25 n 86;
valid +0.295R t 3.18 n 38. NOT scored on the locked holdouts. Research finalist only, not live.
Educational only - not financial advice."""
import numpy as np

SIDE = "short"
GEOM = "t1s1"
LAYERS = ['close crosses above the 5-min SMA50 on this bar', 'stock up > 3% from the open', 'RSI(14) <= 30', '09:50-15:00 ET (bar close)']


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
    sma50 = col('sma50_dist_pct')
    fo = col('fromOpen')
    tod = col('tod')
    p_sma50 = prev(sma50)
    with np.errstate(invalid="ignore"):
        return (sma50 > 0) & (p_sma50 <= 0) & (fo > 3) & (rsi <= 30) & (tod >= 950) & (tod <= 1500)
