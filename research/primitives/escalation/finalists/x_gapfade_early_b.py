"""X-gapfade-early-b - gap fade continuation, early, fewer layers (short, t1s05). Escalation study.
Educational only - not financial advice. Big gap-up (>2%) that is already below its open and VWAP, RSI < 35 and
sellers in control, 09:50-10:30."""
import numpy as np
from _common import col, window

SIDE = "short"
GEOM = "t1s05"
LAYERS = ["gap > 2%", "fromOpen < 0", "vwapDistPct < 0", "rsi(14) < 35", "flow3 < 0 (sellers on the last 3 bars)",
          "time window 09:50-10:30 ET (bar close)"]


def mask(df) -> np.ndarray:
    with np.errstate(invalid="ignore"):
        return ((col(df, "gap") > 2) & (col(df, "fromOpen") < 0) & (col(df, "vwapDistPct") < 0)
                & (col(df, "rsi") < 35) & (col(df, "flow3") < 0) & window(df, 950, 1030))
