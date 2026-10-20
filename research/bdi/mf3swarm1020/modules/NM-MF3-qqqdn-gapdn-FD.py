"""NM-MF3-qqqdn-gapdn-FD - NEAR-MISS (did NOT pass the mf3swarm1020 candidate rule) of MF3-open-flowsell-rsi5hi-FD,
"Early Sellers into a Pop (index down, no gap up)". Forward observation only, if the owner wants it in Testing.
Parent mask (research/bdi/fullday/MF3-open-flowsell-rsi5hi-FD.py) + two layers: QQQ below its open at the decision bar
(lab context qqq_fo, YAML `context: [qqq_fo]`) and the stock did not gap up (gap <= 0).
Open 2-year history (research/bdi/mf3swarm1020, production cost, 5-min path simulator, locked block never loaded):
  train (<= 2025-12) n 991, -0.010R, day-t -0.27 | valid (2026-01..10-07) n 1,108, -0.010R, day-t -0.20 | ~4.9 trades/day
  parent P-FD: train -0.099R, valid -0.051R. Excess vs same-minute random short +0.037R (day-t 1.76).
  Regime: up sessions -0.256R (n 369), flat -0.034R, down +0.089R (n 1,074) - fails the regime gate; walk-forward 0.47.
87 configurations tried in the study (bar 2.99; MF-family lineage bar 4.86). Not a candidate: expectancy is not > 0.
Run with min_adv 95000000, window [950, 1500], context [qqq_fo]. Educational only - not financial advice."""
import numpy as np

SIDE = "short"
GEOM = "t1s1"
LAYERS = [
    "heat <= -30 (a MarcoFlow bearish heat signal; direction = sign of heat)",
    "buyPressure < -0.25 (signed volume, 19 bars; MarcoFlow flow-sell)",
    "RSI(5) > 70 (MarcoFlow rsi5-high)",
    "QQQ below its open at the decision bar (lab context qqq_fo < 0)",
    "no gap up (gap <= 0)",
    "full day: bar close 09:50-15:00 ET (YAML window [950, 1500])",
]


def mask(df) -> np.ndarray:
    heat = df["heat"].to_numpy(dtype=float)
    buyPressure = df["buyPressure"].to_numpy(dtype=float)
    rsi5 = df["rsi5"].to_numpy(dtype=float)
    gap = df["gap"].to_numpy(dtype=float)
    if "qqq_fo" not in df:
        return np.zeros(len(df), bool)          # fail safe: no context column, no signal
    qqq_fo = df["qqq_fo"].to_numpy(dtype=float)
    with np.errstate(invalid="ignore"):
        return (heat <= -30) & (buyPressure < -0.25) & (rsi5 > 70) & (qqq_fo < 0) & (gap <= 0)
