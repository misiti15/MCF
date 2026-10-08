"""RW2-exhaustion-noon-adv150-short - BDI rule-18 rework 2026-10-08 (research/bdi/rework1008). exhaustion_short opened to 12:00 on ADV >= 150M names.
Lineage: exhaustion_short (volume_flip_1). Side short, exit t1s1 (R = 0.25 x daily ATR, exit by 15:55). Indicators on 5-minute bars.
Run with min_adv 150000000 and window [1200, 1500] (bar close ET).
Lab (train 06-30..08-25 / valid 08-26..09-15, production haircut): train +0.137R t 1.73 n 939;
valid +0.128R t 1.89 n 145. NOT scored on the locked holdouts. Research finalist only, not live.
Educational only - not financial advice."""
import numpy as np

SIDE = "short"
GEOM = "t1s1"
LAYERS = ['RSI(5) > 90', 'close > 1% above the 5-min SMA20', 'bearish RSI divergence (20-bar high, RSI(14) > 5 below its 20-bar max)', '12:00-15:00 ET (bar close)', 'ADV >= 150M (set min_adv in the YAML)']


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
    sma20 = col('sma20_dist_pct')
    bdiv = col('bear_div')
    tod = col('tod')
    with np.errstate(invalid="ignore"):
        return (rsi5 > 90) & (sma20 > 1.0) & (bdiv > 0) & (tod >= 1200) & (tod <= 1500)
