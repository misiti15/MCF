"""EX1-vwap-reclaim-breadth-t05s1-long - pod1022 harness EXAMPLE (format demo, not a candidate, not proposed).
Long when the stock closes back above its session VWAP on this bar (previous bar below), it is up on the day
(fromOpen > 0.3%), its 5-minute SMA20 is rising, and at least half the universe is above its own VWAP (context:
breadth). Exit t05s1 (target 0.5R, stop 1R, R = 0.25 x daily ATR, flat 15:55), bar close 10:00-13:00.
Educational only - not financial advice."""
import numpy as np
import pandas as pd

SIDE = "long"
GEOM = "t05s1"
WINDOW = (1000, 1300)
CONTEXT = ["breadth"]
LAYERS = ["vwapDistPct crosses above 0 on this bar", "fromOpen > 0.3", "sma20_slope_pct > 0",
          "breadth >= 0.5 [context: breadth]", "10:00-13:00 ET"]


def _prev(x, df):
    """Previous bar of the same symbol-day (NaN on its first row). Works on one live day or the multi-day frame."""
    key = pd.factorize(df["symbol"].astype(str) + "|" + df["date"].astype(str))[0] if "symbol" in df and "date" in df \
        else np.zeros(len(df), np.int64)
    p = np.r_[np.nan, x[:-1]]
    p[np.r_[True, key[1:] != key[:-1]]] = np.nan
    return p


def mask(df) -> np.ndarray:
    if "breadth" not in df:
        return np.zeros(len(df), dtype=bool)          # fail-safe: no context -> no trades
    vd = df["vwapDistPct"].to_numpy(float)
    tod = df["tod"].to_numpy(float)
    with np.errstate(invalid="ignore"):
        m = (vd > 0) & (_prev(vd, df) <= 0)
        m &= df["fromOpen"].to_numpy(float) > 0.3
        m &= df["sma20_slope_pct"].to_numpy(float) > 0
        m &= df["breadth"].to_numpy(float) >= 0.5
        m &= (tod >= WINDOW[0]) & (tod <= WINDOW[1])
    return np.asarray(m, dtype=bool)
