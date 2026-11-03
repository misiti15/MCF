"""MC4-redrun-outside-reversal-long - ex30/micro microstructure setup (BDI 2026-11-03, research/bdi/ex30/micro).
Same-colour run exhaustion: six red 5-minute bodies in a row, then a green bar that closes above the previous bar's
high; buy for a half-R target. Bar colour is recovered from the wick columns (frames carry no bar open).
Exploratory account candidate; see NOTES.md there. Educational only - not financial advice."""
import numpy as np
import micro_lib as L

SIDE = "long"
GEOM = "t05s1"
WINDOW = (1030, 1500)
N = 6
LAYERS = [
    "the 6 previous bars all have red bodies (body >= 5% of range)",
    "this bar is green and closes above the previous bar's high",
    "bar close 10:30-15:00 ET",
]


def mask(df, n=N) -> np.ndarray:
    seg = L.segments(df)
    c, h, tod = L.col(df, "close"), L.col(df, "high"), L.col(df, "tod")
    k = L.colour(df).astype(float)
    with np.errstate(invalid="ignore"):
        run = np.ones(len(df), bool)
        for j in range(1, n + 1):
            run &= L.lag(k, seg, j) == -1
        m = run & (k == 1) & (c > L.lag(h, seg, 1))
        return np.asarray(m & (tod >= WINDOW[0]) & (tod <= WINDOW[1]), bool)
