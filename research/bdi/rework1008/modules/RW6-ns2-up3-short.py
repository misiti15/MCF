"""RW6-ns2-up3-short - BDI rule-18 rework 2026-10-08 (research/bdi/rework1008). NS2 with the move-from-open floor raised from 2% to 3%.
Lineage: NS2-sma50break-overbought-short. Side short, exit t1s1 (R = 0.25 x daily ATR, exit by 15:55). Indicators on 5-minute bars.
Run with min_adv 95000000 and window [950, 1130] (bar close ET).
Lab (train 06-30..08-25 / valid 08-26..09-15, production haircut): train +0.098R t 0.78 n 217;
valid +0.203R t 2.34 n 45. NOT scored on the locked holdouts. Research finalist only, not live.
Educational only - not financial advice."""
import numpy as np

SIDE = "short"
GEOM = "t1s1"
LAYERS = ['close crosses above the 5-min SMA50 on this bar', 'stock up > 3% from the open', 'RSI(14) >= 60', '09:50-11:30 ET (bar close)']


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
        return (sma50 > 0) & (p_sma50 <= 0) & (fo > 3) & (rsi >= 60) & (tod >= 950) & (tod <= 1130)
