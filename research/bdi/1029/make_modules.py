"""Writes the 8 pre-registered Move Hunt precursor modules (MH1 in-play continuation, long + short) for pod1022's
score_batch.py. Grid fixed before any 2-year number was seen: vol_exp floor {0.12, 0.17} x GEOM {hold, holdtr} x side.
vol_exp = 5-minute ATR(14) % / daily ATR % (atrPct / (atr_d / close x 100)): the Move Hunt's strongest one-day precursor
of a >= 0.5 ATR move within 90 min (3.5x lift in the top quintile, both sides). Direction comes from the day's trend:
long = fromOpen > 0, RSI14 >= 65, buyPressure > 0.2; short = the mirror. Educational only - not financial advice."""
from pathlib import Path
T = '''"""{name} - Move Hunt 2026-10-29 precursor test (research/bdi/1029). {side} when the stock is "in play" (5-minute ATR
>= {q} x its daily ATR) and trending its way on the day (fromOpen {fo}, RSI14 {rsi}, buyPressure {bp}). GEOM {geom}
(stop 1R = 0.25 daily ATR; holdtr trails 1R once +1R; flat 15:55). ADV20 >= $95M (live lab floor). 09:50-15:00.
Educational only - not financial advice."""
import numpy as np
SIDE = "{side}"
GEOM = "{geom}"
WINDOW = (950, 1500)
MIN_ADV = 95e6
LAYERS = ["vol_exp >= {q}", "fromOpen {fo}", "rsi {rsi}", "buyPressure {bp}"]


def mask(df) -> np.ndarray:
    c = df["close"].to_numpy(float); atr = df["atr_d"].to_numpy(float)
    with np.errstate(invalid="ignore", divide="ignore"):
        ve = df["atrPct"].to_numpy(float) / (atr / c * 100)
        m = ve >= {q}
        m &= df["fromOpen"].to_numpy(float) {fo}
        m &= df["rsi"].to_numpy(float) {rsi}
        m &= df["buyPressure"].to_numpy(float) {bp}
    return np.asarray(m, dtype=bool)
'''
for side, fo, rsi, bp in (("long", "> 0", ">= 65", "> 0.2"), ("short", "< 0", "<= 35", "< -0.2")):
    for q in ("0.12", "0.17"):
        for geom in ("hold", "holdtr"):
            name = f"MH1-inplay-q{q[2:]}-{geom}-{side}"
            Path(f"modules/{name}.py").write_text(T.format(name=name, side=side, q=q, fo=fo, rsi=rsi, bp=bp, geom=geom))
print("8 modules")
