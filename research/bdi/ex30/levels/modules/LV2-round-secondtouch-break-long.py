"""LV2-round-secondtouch-break-long - ex30/levels price-level setup (BDI 2026-11-03, research/bdi/ex30/levels).
Second-touch break of a round number: price had already reached the round number R earlier today without running
through it (running high before this bar within R - 0.05 .. R + 0.10 ATR), traded >= 0.40 ATR below R during the last
6 bars, and now closes back above R (previous close below R). Long at the bar close. Exploratory account candidate.
Educational only - not financial advice."""
import numpy as np
import levels_lib as L

SIDE = "long"
GEOM = "t1s1"
WINDOW = (1030, 1500)
LAYERS = [
    "close crosses above round number R = grid level at or below the close (previous close < R)",
    "running high before this bar within [R - 0.05 ATR, R + 0.10 ATR] (R touched before, never cleared)",
    "lowest low of the previous 6 bars <= R - 0.40 ATR (pulled away before the second attempt)",
    "bar close 10:30-15:00 ET",
]


def mask(df, pull=0.40) -> np.ndarray:
    seg = L.segments(df)
    lv = L.levels(df)
    c, l, atr = L.col(df, "close"), L.col(df, "low"), L.col(df, "atr_d")
    with np.errstate(invalid="ignore", divide="ignore"):
        st = L.step(c)
        R = np.floor(c / st) * st
        hp = L.lag(lv["hod"], seg, 1)
        lo6 = np.fmin.reduce([L.lag(l, seg, j) for j in range(1, 7)])
        ok6 = np.isfinite(L.lag(l, seg, 6))
        m = (L.lag(c, seg, 1) < R) & (c >= R) & (hp >= R - 0.05 * atr) & (hp <= R + 0.10 * atr) & ok6 & \
            (lo6 <= R - pull * atr)
    return np.asarray(m & L.window(df, WINDOW), bool)
