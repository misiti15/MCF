"""X-failbo - failed breakout short on gap-ups (short, t1s1). Escalation study.
Educational only - not financial advice. Gap-up (>1%) that ran >= 0.75 daily ATR above its open, has given back
>= 0.6 ATR from the high of day, is back below +0.3 ATR from the open and below VWAP with falling momentum,
10:00-11:00 (approximates 'back inside the opening range after breaking above')."""
import numpy as np
from _common import atr_units, col, hod_above_open_atr, window

SIDE = "short"
GEOM = "t1s1"
LAYERS = ["gap > 1%", "HOD >= 0.75 ATR above the open", "dist_hod_atr >= 0.6 (gave back 0.6 ATR)",
          "fromOpen < +0.3 ATR", "vwapDistPct < -0.25%", "momentum < -0.5", "time window 10:00-11:00 ET (bar close)"]


def mask(df) -> np.ndarray:
    with np.errstate(invalid="ignore"):
        return ((col(df, "gap") > 1) & (hod_above_open_atr(df) >= 0.75) & (col(df, "dist_hod_atr") >= 0.6)
                & (atr_units(df, "fromOpen") < 0.3) & (col(df, "vwapDistPct") < -0.25)
                & (col(df, "momentum") < -0.5) & window(df, 1000, 1100))
