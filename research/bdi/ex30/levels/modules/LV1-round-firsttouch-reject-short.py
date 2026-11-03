"""LV1-round-firsttouch-reject-short - ex30/levels price-level setup (BDI 2026-11-03, research/bdi/ex30/levels).
The FIRST time today price reaches a round number from below (the running high before this bar was under it), the
bar is rejected: it closes >= 0.05 ATR back below the round number with an upper wick >= 40% of its range.
Short at the bar close. Exploratory account candidate; see NOTES.md there. Educational only - not financial advice."""
import numpy as np
import levels_lib as L

SIDE = "short"
GEOM = "t05s1"
WINDOW = (1000, 1500)
LAYERS = [
    "round number R = next grid level above the running high of day before this bar ($10 >= $200, $5 >= $50, $1 >= $10, $0.50)",
    "this bar's high >= R (first touch of R today)",
    "close <= R - 0.05 ATR and upper_wick >= 0.40",
    "bar close 10:00-15:00 ET",
]


def mask(df, wick=0.40) -> np.ndarray:
    seg = L.segments(df)
    lv = L.levels(df)
    h, c, atr = L.col(df, "high"), L.col(df, "close"), L.col(df, "atr_d")
    with np.errstate(invalid="ignore", divide="ignore"):
        hp = L.lag(lv["hod"], seg, 1)
        st = L.step(hp)
        R = (np.floor(hp / st) + 1) * st
        m = (h >= R) & (c <= R - 0.05 * atr) & (L.col(df, "upper_wick") >= wick)
    return np.asarray(m & L.window(df, WINDOW), bool)
