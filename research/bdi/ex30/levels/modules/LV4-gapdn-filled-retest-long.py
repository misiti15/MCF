"""LV4-gapdn-filled-retest-long - ex30/levels price-level setup (BDI 2026-11-03, research/bdi/ex30/levels).
Filled gap turns into support: on a gap-down day (gap <= -1%) the running high has already reached the prior close
(gap filled), and now a bar dips back to within 0.10 ATR of the prior close and closes >= 0.02 ATR above it (the level
holds on the retest). Long at the bar close. Exploratory account candidate. Educational only - not financial advice."""
import numpy as np
import levels_lib as L

SIDE = "long"
GEOM = "t05s1"
WINDOW = (1015, 1500)
LAYERS = [
    "gap <= -1.0% (today's open vs prior close)",
    "running high before this bar >= prior close (gap filled earlier today)",
    "low <= prior close + 0.10 ATR and close >= prior close + 0.02 ATR (retest holds)",
    "bar close 10:15-15:00 ET",
]


def mask(df, gmax=-1.0) -> np.ndarray:
    seg = L.segments(df)
    lv = L.levels(df)
    c, l, atr, g = L.col(df, "close"), L.col(df, "low"), L.col(df, "atr_d"), L.col(df, "gap")
    pc = lv["pclose"]
    with np.errstate(invalid="ignore", divide="ignore"):
        m = (g <= gmax) & (L.lag(lv["hod"], seg, 1) >= pc) & (l <= pc + 0.10 * atr) & (c >= pc + 0.02 * atr)
    return np.asarray(m & L.window(df, WINDOW), bool)
