"""LV3-gapup-halffill-short - ex30/levels price-level setup (BDI 2026-11-03, research/bdi/ex30/levels).
Gap-fill magnet: on a +1.5..+8% gap-up day, the first close through the half-gap line (midpoint of today's open and
the prior close) from above, below session VWAP, with >= 0.30 ATR still left to the prior close. Short at the bar
close, aiming at the unfilled half of the gap. Exploratory account candidate. Educational only - not financial advice."""
import numpy as np
import levels_lib as L

SIDE = "short"
GEOM = "t1s1"
WINDOW = (1000, 1400)
LAYERS = [
    "gap +1.5% .. +8% (today's open vs prior close)",
    "close crosses below the half-gap line (prior close + 0.5 x (open - prior close)); previous close above it",
    "close below session VWAP and close - prior close >= 0.30 ATR (room left to the fill)",
    "bar close 10:00-14:00 ET",
]


def mask(df, gmin=1.5) -> np.ndarray:
    seg = L.segments(df)
    lv = L.levels(df)
    c, atr, g = L.col(df, "close"), L.col(df, "atr_d"), L.col(df, "gap")
    with np.errstate(invalid="ignore", divide="ignore"):
        half = lv["pclose"] + 0.5 * (lv["open"] - lv["pclose"])
        m = (g >= gmin) & (g <= 8.0) & (c <= half) & (L.lag(c, seg, 1) > half) & (c < lv["vwap"]) & \
            (c - lv["pclose"] >= 0.30 * atr)
    return np.asarray(m & L.window(df, WINDOW), bool)
