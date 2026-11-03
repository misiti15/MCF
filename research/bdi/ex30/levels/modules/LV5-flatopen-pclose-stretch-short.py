"""LV5-flatopen-pclose-stretch-short - ex30/levels price-level setup (BDI 2026-11-03, research/bdi/ex30/levels).
Prior close as a magnet on flat-open days: the stock opened within +-0.4% of the prior close, has since stretched
>= 1.0 ATR above the prior close, prints a new high of day (within 0.05 ATR of it) on below-average volume after
11:30. Short at the bar close, betting on the drift back toward the prior close. Exploratory account candidate.
Educational only - not financial advice."""
import numpy as np
import levels_lib as L

SIDE = "short"
GEOM = "t1s1"
WINDOW = (1130, 1500)
LAYERS = [
    "|gap| <= 0.4% (flat open vs prior close)",
    "close >= prior close + 1.0 ATR",
    "dist_hod_atr <= 0.05 (at the high of day) and volumeRatio < 1.0",
    "bar close 11:30-15:00 ET",
]


def mask(df, stretch=1.0) -> np.ndarray:
    lv = L.levels(df)
    c, atr, g = L.col(df, "close"), L.col(df, "atr_d"), L.col(df, "gap")
    with np.errstate(invalid="ignore", divide="ignore"):
        m = (np.abs(g) <= 0.4) & (c >= lv["pclose"] + stretch * atr) & (L.col(df, "dist_hod_atr") <= 0.05) & \
            (L.col(df, "volumeRatio") < 1.0)
    return np.asarray(m & L.window(df, WINDOW), bool)
