"""XS1-laggard-greentape-short - ex30/xsec cross-sectional rank-proxy setup (BDI 2026-11-03, research/bdi/ex30/xsec).
Shorts a name that is in the universe's weak tail while the tape is green: >= 65% of the universe is above its open,
SPY is up from its open, yet this name is >= 0.75 daily ATR below its own open and under its VWAP.
Needs lab context columns (YAML `context: [breadth_open, spy_fo]`); a missing column gives NaN -> no signal (fail safe).
Exploratory account candidate; see research/bdi/ex30/xsec/NOTES.md. Educational only - not financial advice."""
import numpy as np

SIDE = "short"
GEOM = "t1s1"
WINDOW = (1000, 1400)
CONTEXT = ['breadth_open', 'spy_fo']
LAYERS = [
    'breadth_open >= 0.65 (>= 65% of the universe above its open)',
    'spy_fo > 0 (SPY above its open)',
    'move from open <= -0.75 daily ATR',
    'close < session VWAP',
    'bar close 10:00-14:00 ET',
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
        m = (col('breadth_open') >= 0.65) & (col('spy_fo') > 0) & (move <= -0.75) & (vwd < 0)
        return np.asarray(m & (tod >= WINDOW[0]) & (tod <= WINDOW[1]), bool)
