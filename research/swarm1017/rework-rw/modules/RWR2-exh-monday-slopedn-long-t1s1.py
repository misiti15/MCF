"""RWR2-exh-monday-slopedn-long-t1s1 - rework of exhaustion_short(-FD) (swarm1017/rework-rw, 2026-10-17).
OPPOSITE side of the exhaustion signal (RSI5 > 90, > 1% above the 5-min SMA20, bearish RSI divergence): LONG it, on
Mondays only, when the 5-min SMA20 slope is still negative; bar close 09:50-15:00, target 1R / stop 1R.
Open history, production cost (prod_r, tod entry costs), first signal per symbol-day, min_adv 95M, no prefilter:
  train 2024-10..2025-12 (locked excluded): n 267, exp +0.171R, day-t 2.84
  valid 2026-01..2026-10-07: n 134, exp +0.231R, day-t 2.00; all n 401 (67 sessions), exp +0.191R, day-t 3.63
  regime up/flat/down +0.261/-0.038/+0.039R (n up 297, down 40: pass, thin in down), walk-forward 0.67,
  ex-best-day +0.151R, excess vs same-minute random +0.128R (t 2.54).
STATUS: FAILS the try-count bar (t 3.63 < 5.25). A day-of-week x filter pair picked out of 132,892 configurations and
mostly an up-session effect: likely noise. Not for live funds. Research record only.
Live note: implementable as type: lab (no prefilter); day-of-week needs the frame's DatetimeIndex or a `date` column.
Educational only - not financial advice."""
import numpy as np
import pandas as pd

SIDE = "long"
GEOM = "t1s1"
LAYERS = [
    "RSI(5) > 90",
    "close > 1% above the 5-min SMA20",
    "bearish RSI divergence (bear_div)",
    "5-min SMA20 slope < 0",
    "Monday session",
    "window: bar close 09:50-15:00 ET (YAML window [950, 1500]); no prefilter",
]


def _dow(df) -> np.ndarray:
    if "date" in df.columns:
        return pd.to_datetime(df["date"]).dt.dayofweek.to_numpy()
    return pd.DatetimeIndex(df.index).dayofweek.to_numpy()


def mask(df) -> np.ndarray:
    c = {k: df[k].to_numpy(dtype=float) for k in ("rsi5", "sma20_dist_pct", "bear_div", "sma20_slope_pct", "tod")}
    with np.errstate(invalid="ignore"):
        return ((c["rsi5"] > 90) & (c["sma20_dist_pct"] > 1.0) & (c["bear_div"] > 0) & (c["sma20_slope_pct"] < 0)
                & (_dow(df) == 0) & (c["tod"] >= 950) & (c["tod"] <= 1500))
