"""XS4-quiet-bottomoutlier-fade-long - ex30/xsec cross-sectional rank-proxy setup (BDI 2026-11-03, research/bdi/ex30/xsec).
Quiet-tape fade of the bottom outlier: SPY within +-0.25% of its open and the universe split (35-65% above VWAP), while
this name's move from open trails SPY's by >= 1 daily ATR; buy on the first up bar.
Needs lab context columns (YAML `context: [breadth, spy_fo]`); a missing column gives NaN -> no signal (fail safe).
Exploratory account candidate; see research/bdi/ex30/xsec/NOTES.md. Educational only - not financial advice."""
import numpy as np

SIDE = "long"
GEOM = "t1s1"
WINDOW = (1030, 1430)
CONTEXT = ['breadth', 'spy_fo']
LAYERS = [
    'abs(spy_fo) <= 0.25 (quiet tape so far)',
    '0.35 <= breadth <= 0.65 (balanced universe)',
    'excess move vs SPY <= -1.0 ATR',
    'close > previous 5-minute close',
    'bar close 10:30-14:30 ET',
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
        m = (np.abs(col('spy_fo')) <= 0.25) & (b >= 0.35) & (b <= 0.65) & (excess <= -1.0) & (c > prev(c))
        return np.asarray(m & (tod >= WINDOW[0]) & (tod <= WINDOW[1]), bool)
