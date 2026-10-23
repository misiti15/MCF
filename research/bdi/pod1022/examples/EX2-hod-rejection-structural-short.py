"""EX2-hod-rejection-structural-short - pod1022 harness EXAMPLE (format demo, not a candidate, not proposed).
Short a rejection at the high of day: the bar's high is within 0.05 daily ATR of the day's high so far, it closes in
the lower half of its range with an upper wick >= 50% of the range, the stock is > 2% above its open, RSI(14) >= 65.
Structural exit (GEOM "S"): stop 1c above the signal bar's high (plus 0.02 daily ATR), target 1.5x the entry-to-stop
risk, flat 15:55. Bar close 10:30-14:30. Shows stop_price / target_price.
Educational only - not financial advice."""
import numpy as np

SIDE = "short"
GEOM = "S"
WINDOW = (1030, 1430)
TARGET_MULT = 1.5
LAYERS = ["bar high within 0.05 ATR of the high of day", "upper wick >= 50% of the bar range",
          "close in the lower half of the bar", "fromOpen > 2", "rsi >= 65", "10:30-14:30 ET",
          "stop above the bar high + 0.02 ATR, target 1.5R structural, flat 15:55"]


def mask(df) -> np.ndarray:
    h, l, c = (df[k].to_numpy(float) for k in ("high", "low", "close"))
    tod = df["tod"].to_numpy(float)
    rng = h - l
    with np.errstate(invalid="ignore", divide="ignore"):
        hod = c + df["dist_hod_atr"].to_numpy(float) * df["atr_d"].to_numpy(float)    # running high of day
        m = (hod - h) <= 0.05 * df["atr_d"].to_numpy(float)
        m &= df["upper_wick"].to_numpy(float) >= 0.5
        m &= (c - l) <= 0.5 * rng
        m &= df["fromOpen"].to_numpy(float) > 2
        m &= df["rsi"].to_numpy(float) >= 65
        m &= (tod >= WINDOW[0]) & (tod <= WINDOW[1])
    return np.asarray(m, dtype=bool)


def stop_price(f, i):
    return float(f["high"].iloc[i]) + 0.01 + 0.02 * float(f["atr_d"].iloc[i])


def target_price(f, i, stop):
    px = float(f["close"].iloc[i])
    return px - TARGET_MULT * (stop - px)
