"""X-vwaploss-run - confirmation short: a gap-up runner loses VWAP (short, t1s1). Escalation study.
Educational only - not financial advice. Gap-up that ran >= 1 daily ATR above its open, is now >= 0.4 ATR off
the high and has just crossed below VWAP (within 3 bars) on above-average volume, 10:00-13:00. The confirmation
version of 'short the overbought name': wait for the VWAP loss instead of fading the rip."""
import numpy as np
from _common import col, hod_above_open_atr, window

SIDE = "short"
GEOM = "t1s1"
LAYERS = ["gap > 0", "HOD >= 1.0 ATR above the open", "dist_hod_atr >= 0.4", "vwapReclaim == -1 (crossed below VWAP within 3 bars)",
          "volumeRatio > 1.5", "time window 10:00-13:00 ET (bar close)"]


def mask(df) -> np.ndarray:
    with np.errstate(invalid="ignore"):
        return ((col(df, "gap") > 0) & (hod_above_open_atr(df) >= 1.0) & (col(df, "dist_hod_atr") >= 0.4)
                & (col(df, "vwapReclaim") == -1) & (col(df, "volumeRatio") > 1.5) & window(df, 1000, 1300))
