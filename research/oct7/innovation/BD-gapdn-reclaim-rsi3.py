"""BD-gapdn-reclaim-rsi3 (BD innovation 2026-10-08) - SHORT, t1s1, 13:00-14:30 ET bar closes.
The exact stage-2 winner: BD-gapdn-reclaim plus a short-horizon RSI(3) >= 70 timing layer (sell the
bounce bar). The ablation shows RSI(3) is not needed (BD-gapdn-reclaim scores better on valid), so score
this one only if the lead prefers the exact stage-2 version; it would be look 3 of the gap lineage (t >= 2.0).
Train: n 4152, +0.072R prod, t_day 1.57 (best day = 84% of total, ex-best +0.013R). Valid: n 2104, +0.159R,
t_day 1.13, ex-best +0.125R. Educational only - not financial advice."""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _bd_features as F  # noqa: E402

SIDE = "short"
GEOM = "t1s1"
LAYERS = [
    "gap <= -0.88% (opened at least 0.88% below the prior close)",
    "fromOpen > 0 (now trading above today's open)",
    "RSI(3) of 5-minute closes >= 70 (restarted each session)",
    "time window 13:00-14:30 ET (bar close)",
]


def mask(df) -> np.ndarray:
    gap = df["gap"].to_numpy(dtype=float)
    fo = df["fromOpen"].to_numpy(dtype=float)
    tod = df["tod"].to_numpy(dtype=float)
    r3 = df["rsi3"].to_numpy(dtype=float) if "rsi3" in df.columns else F.rsi(df, 3)
    return (gap <= -0.88) & (fo > 0) & (r3 >= 70) & (tod >= 1300) & (tod <= 1430)
