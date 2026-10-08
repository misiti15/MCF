"""NS3-failed-vwap-reclaim-short - owner-directed setup 2026-10-08 from the 'obvious metrics before big moves' scan (research/owner1008).
Side short, exit t1s1 (R = 0.25 x daily ATR, exit by 15:55). Indicators on 5-minute bars.
Train/valid only (scan.csv); PROBATION in the primary account at the owner's request. Educational only - not financial advice."""
import numpy as np

SIDE = "short"
GEOM = "t1s1"
LAYERS = ['price reclaims VWAP on this bar', 'price above the 5-min 50-bar average', 'stock down > 2% from the open', '09:50-11:30 ET']


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
        return (vwap > 0) & (prev('vwapDistPct') <= 0) & (sma50 > 0) & (fromOpen < -2) & (tod >= 950) & (tod <= 1130)
