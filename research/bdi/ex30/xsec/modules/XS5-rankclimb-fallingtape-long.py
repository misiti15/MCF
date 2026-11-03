"""XS5-rankclimb-fallingtape-long - ex30/xsec cross-sectional rank-proxy setup (BDI 2026-11-03, research/bdi/ex30/xsec).
Rank change: the universe is losing VWAP (breadth down >= 0.15 over 3 bars) while this name gains on its VWAP over the
same 3 bars and reclaims it on this bar - it climbs the cross-section while the field falls.
Needs lab context columns (YAML `context: [breadth]`); a missing column gives NaN -> no signal (fail safe).
Exploratory account candidate; see research/bdi/ex30/xsec/NOTES.md. Educational only - not financial advice."""
import numpy as np

SIDE = "long"
GEOM = "t05s1"
WINDOW = (1000, 1500)
CONTEXT = ['breadth']
LAYERS = [
    'breadth - breadth 3 bars ago <= -0.15 (field losing VWAP)',
    'vwapDistPct - its value 3 bars ago > 0',
    'prev vwapDistPct <= 0 and now > 0 (VWAP reclaim)',
    'bar close 10:00-15:00 ET',
]


def mask(df) -> np.ndarray:
    def col(k):
        return df[k].to_numpy(dtype=float) if k in df else np.full(len(df), np.nan)

    def prev(x, n=1):
        p = np.r_[np.full(n, np.nan), x[:-n]]
        if "symbol" in df and "date" in df:     # offline frames hold many symbol-days: no carry-over
            key = df["symbol"].astype(str).to_numpy() + "|" + df["date"].astype(str).to_numpy()
            for j in range(1, n + 1):
                p[np.r_[np.ones(j, bool), key[j:] != key[:-j]]] = np.nan
        return p

    c, atr, fo, vwd, tod = col("close"), col("atr_d"), col("fromOpen"), col("vwapDistPct"), col("tod")
    with np.errstate(invalid="ignore", divide="ignore"):
        move = (c - c / (1 + fo / 100)) / atr
        excess = (fo - col("spy_fo")) / (atr / c * 100)
        b = col('breadth')
        m = (b - prev(b, 3) <= -0.15) & (vwd - prev(vwd, 3) > 0) & (prev(vwd) <= 0) & (vwd > 0)
        return np.asarray(m & (tod >= WINDOW[0]) & (tod <= WINDOW[1]), bool)
