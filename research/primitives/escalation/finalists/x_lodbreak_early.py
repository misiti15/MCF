"""X-lodbreak-early - short the drop: new low of day, early (short, t1s05). Escalation study.
Educational only - not financial advice. MarcoFlow's lesson as a mask: within 0.05 ATR of the low of day, >= 0.5 ATR
below the open, below VWAP, volume > 2x, not yet oversold (RSI > 25), 09:50-10:30."""
import numpy as np
from _common import atr_units, col, window

SIDE = "short"
GEOM = "t1s05"
LAYERS = ["dist_lod_atr <= 0.05 (at the low of day)", "fromOpen < -0.5 ATR", "below VWAP", "volumeRatio > 2",
          "rsi(14) > 25", "time window 09:50-10:30 ET (bar close)"]


def mask(df) -> np.ndarray:
    with np.errstate(invalid="ignore"):
        return ((col(df, "dist_lod_atr") <= 0.05) & (atr_units(df, "fromOpen") < -0.5) & (col(df, "vwapDistPct") < 0)
                & (col(df, "volumeRatio") > 2) & (col(df, "rsi") > 25) & window(df, 950, 1030))
