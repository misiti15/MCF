"""MC1-nr7-expansion-volburst-long - ex30/micro microstructure setup (BDI 2026-11-03, research/bdi/ex30/micro).
Compression then expansion on 5-minute bars: the previous bar was the narrowest of the last 7 (NR7); this bar breaks
its high, closes near its own top, on >= 1.5x volume. Exploratory account candidate; see NOTES.md there.
Educational only - not financial advice."""
import numpy as np
import micro_lib as L

SIDE = "long"
GEOM = "t1s1"
WINDOW = (1045, 1500)
K = 7
LAYERS = [
    "previous bar's range is the narrowest of the last 7 bars (NR7)",
    "close > previous bar's high and upper_wick <= 0.25",
    "volumeRatio >= 1.5",
    "bar close 10:45-15:00 ET",
]


def mask(df, k=K, vr_min=1.5) -> np.ndarray:
    seg = L.segments(df)
    c, h, l, atr, tod = L.col(df, "close"), L.col(df, "high"), L.col(df, "low"), L.col(df, "atr_d"), L.col(df, "tod")
    with np.errstate(invalid="ignore", divide="ignore"):
        rng = (h - l) / atr
        r1 = L.lag(rng, seg, 1)
        nr = np.isfinite(r1)
        for j in range(2, k + 1):
            nr &= r1 <= L.lag(rng, seg, j)
        m = nr & (c > L.lag(h, seg, 1)) & (L.col(df, "upper_wick") <= 0.25) & (L.col(df, "volumeRatio") >= vr_min)
        return np.asarray(m & (tod >= WINDOW[0]) & (tod <= WINDOW[1]), bool)
