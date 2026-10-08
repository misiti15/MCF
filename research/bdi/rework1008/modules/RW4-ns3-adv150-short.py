"""RW4-ns3-adv150-short - BDI rule-18 rework 2026-10-08 (research/bdi/rework1008). NS3 failed VWAP reclaim, ADV >= 150M only.
Lineage: NS3-failed-vwap-reclaim-short. Side short, exit t1s1 (R = 0.25 x daily ATR, exit by 15:55). Indicators on 5-minute bars.
Run with min_adv 150000000 and window [950, 1130] (bar close ET).
Lab (train 06-30..08-25 / valid 08-26..09-15, production haircut): train +0.139R t 1.51 n 176;
valid +0.357R t 1.72 n 35. NOT scored on the locked holdouts. Research finalist only, not live.
Educational only - not financial advice."""
import numpy as np

SIDE = "short"
GEOM = "t1s1"
LAYERS = ['close crosses above VWAP on this bar', 'stock down > 2% from the open', 'close above the 5-min SMA50', '09:50-11:30 ET (bar close)', 'ADV >= 150M (set min_adv in the YAML)']


def mask(df) -> np.ndarray:
    def col(k):
        return df[k].to_numpy(dtype=float)

    def prev(x):
        p = np.r_[np.nan, x[:-1]]
        if "symbol" in df and "date" in df:     # offline frames hold many symbol-days: no carry-over
            key = df["symbol"].astype(str).to_numpy() + "|" + df["date"].astype(str).to_numpy()
            p[np.r_[True, key[1:] != key[:-1]]] = np.nan
        return p

    sma50 = col('sma50_dist_pct')
    vwap = col('vwapDistPct')
    fo = col('fromOpen')
    tod = col('tod')
    p_vwap = prev(vwap)
    with np.errstate(invalid="ignore"):
        return (vwap > 0) & (p_vwap <= 0) & (fo < -2) & (sma50 > 0) & (tod >= 950) & (tod <= 1130)
