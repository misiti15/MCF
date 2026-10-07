"""X-gapfade-early - gap fade continuation, early (short, t1s05). Escalation study (key escalation).
Educational only - not financial advice. Gap-up names already below the open and well below VWAP, oversold and
still falling on volume, 09:50-10:30: short the drop (MarcoFlow lesson) - early, not at 11:05."""
import numpy as np
from _common import col, window

SIDE = "short"
GEOM = "t1s05"
LAYERS = ["gap > 1%", "fromOpen < 0", "vwapDistPct < -0.5%", "momentum < -0.5", "rsi(14) < 30",
          "volumeRatio > 1.5", "flow3 < 0 (sellers on the last 3 bars)", "time window 09:50-10:30 ET (bar close)"]


def mask(df) -> np.ndarray:
    with np.errstate(invalid="ignore"):
        return ((col(df, "gap") > 1) & (col(df, "fromOpen") < 0) & (col(df, "vwapDistPct") < -0.5)
                & (col(df, "momentum") < -0.5) & (col(df, "rsi") < 30) & (col(df, "volumeRatio") > 1.5)
                & (col(df, "flow3") < 0) & window(df, 950, 1030))
