"""MC5-firsthour-break-voldecay-short - ex30/micro microstructure setup (BDI 2026-11-03, research/bdi/ex30/micro).
First-hour range break on fading volume: the close crosses above the 09:30-10:30 high while this bar's volume is
below 0.8x its 20-bar mean and the last 5 bars' volume is below the 15 before (volume decay); fade it short.
Exploratory account candidate; see NOTES.md there. Educational only - not financial advice."""
import numpy as np
import pandas as pd
import micro_lib as L

SIDE = "short"
GEOM = "t1s1"
WINDOW = (1035, 1400)
LAYERS = [
    "close crosses above the first-hour high (running high of day at the 10:30 bar; previous close <= it)",
    "volumeRatio < 0.8",
    "volumeSurge < 1.0 (last 5 bars' volume below the prior 15)",
    "bar close 10:35-14:00 ET",
]


def mask(df, vr_max=0.8) -> np.ndarray:
    seg = L.segments(df)
    c, atr, tod = L.col(df, "close"), L.col(df, "atr_d"), L.col(df, "tod")
    with np.errstate(invalid="ignore"):
        hod = c + L.col(df, "dist_hod_atr") * atr
        h1 = pd.Series(np.where(tod == 1030, hod, np.nan)).groupby(seg).transform("max").to_numpy(dtype=float, copy=True)
        h1[tod <= 1030] = np.nan
        m = (c > h1) & (L.lag(c, seg, 1) <= h1) & (L.col(df, "volumeRatio") < vr_max) & (L.col(df, "volumeSurge") < 1.0)
        return np.asarray(m & (tod >= WINDOW[0]) & (tod <= WINDOW[1]), bool)
