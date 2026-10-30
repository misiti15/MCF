"""MH1-inplay-q17-hold-long - Move Hunt 2026-10-29 precursor test (research/bdi/1029). long when the stock is "in play" (5-minute ATR
>= 0.17 x its daily ATR) and trending its way on the day (fromOpen > 0, RSI14 >= 65, buyPressure > 0.2). GEOM hold
(stop 1R = 0.25 daily ATR; holdtr trails 1R once +1R; flat 15:55). ADV20 >= $95M (live lab floor). 09:50-15:00.
Educational only - not financial advice."""
import numpy as np
SIDE = "long"
GEOM = "hold"
WINDOW = (950, 1500)
MIN_ADV = 95e6
LAYERS = ["vol_exp >= 0.17", "fromOpen > 0", "rsi >= 65", "buyPressure > 0.2"]


def mask(df) -> np.ndarray:
    c = df["close"].to_numpy(float); atr = df["atr_d"].to_numpy(float)
    with np.errstate(invalid="ignore", divide="ignore"):
        ve = df["atrPct"].to_numpy(float) / (atr / c * 100)
        m = ve >= 0.17
        m &= df["fromOpen"].to_numpy(float) > 0
        m &= df["rsi"].to_numpy(float) >= 65
        m &= df["buyPressure"].to_numpy(float) > 0.2
    return np.asarray(m, dtype=bool)
