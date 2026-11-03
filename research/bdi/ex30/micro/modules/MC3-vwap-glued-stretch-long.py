"""MC3-vwap-glued-stretch-long - ex30/micro microstructure setup (BDI 2026-11-03, research/bdi/ex30/micro).
Time at VWAP: a name whose bars have straddled VWAP for >= 60% of the session (since 09:50) is in balance; when it is
pushed >= 0.30 ATR below VWAP on a bar with a long lower wick, buy for a half-R snap back. Built for quiet / range tapes.
Exploratory account candidate; see NOTES.md there. Educational only - not financial advice."""
import numpy as np
import micro_lib as L

SIDE = "long"
GEOM = "t05s1"
WINDOW = (1100, 1500)
LAYERS = [
    "share of bars since 09:50 (incl. this one) whose range straddled VWAP >= 0.60",
    "close <= VWAP - 0.30 x daily ATR",
    "lower_wick >= 0.5",
    "bar close 11:00-15:00 ET",
]


def mask(df, share_min=0.60) -> np.ndarray:
    seg = L.segments(df)
    c, h, l, atr, tod = L.col(df, "close"), L.col(df, "high"), L.col(df, "low"), L.col(df, "atr_d"), L.col(df, "tod")
    with np.errstate(invalid="ignore", divide="ignore"):
        vw = c / (1 + L.col(df, "vwapDistPct") / 100)
        live = tod >= 950
        st = (l <= vw) & (vw <= h) & live
        share = L.seg_cumsum(st, seg) / L.seg_cumsum(live, seg)
        m = (share >= share_min) & ((vw - c) / atr >= 0.30) & (L.col(df, "lower_wick") >= 0.5)
        return np.asarray(m & (tod >= WINDOW[0]) & (tod <= WINDOW[1]), bool)
