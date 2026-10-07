"""X-bottom-div - find the bottom on faded gap-ups (long, t1s1). Escalation study.
Educational only - not financial advice. Instead of buying the 11:05 falling knife: a gap-up (>1%) that is now
more than 2% below its open, only once a bullish RSI divergence prints on a long lower wick with RSI turning up,
12:00-14:30."""
import numpy as np
from _common import col, window

SIDE = "long"
GEOM = "t1s1"
LAYERS = ["gap > 1%", "fromOpen < -2%", "bull_div == 1 (20-bar low while RSI(14) is >5 above its 20-bar min)",
          "lower_wick > 0.6 of the bar range", "rsiSlope > 0 (RSI up over 3 bars)", "time window 12:00-14:30 ET (bar close)"]


def mask(df) -> np.ndarray:
    with np.errstate(invalid="ignore"):
        return ((col(df, "gap") > 1) & (col(df, "fromOpen") < -2) & (col(df, "bull_div") > 0)
                & (col(df, "lower_wick") > 0.6) & (col(df, "rsiSlope") > 0) & window(df, 1200, 1430))
