"""RW3S-gapdn-flowsell-short-FD - simpler twin of RW3-gapdn-rsi5pop-flowsell-short-FD with the RSI(5) > 80 condition removed
(BDI overnight 2026-11-02, research/bdi/night1102/simple). Owner RW3S yes 2026-11-03: Testing observation for 5 live sessions,
then re-evaluate. Did NOT pass BAR90 or the twin bar; it is a down-day bet. Educational only - not financial advice."""
import numpy as np

SIDE = "short"
GEOM = "t1s1"
LAYERS = [
    "MarcoFlow heat <= -20 (bearish)",
    "buyPressure < -0.35 (heavy net selling, 19 bars)",
    "gapped down at the open",
    "full day: bar close 09:50-15:00 ET (YAML window [950, 1500])",
]


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
        return (heat <= -20) & (bp < -0.35) & (gap < 0)
