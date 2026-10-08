"""BD-gapdn-reclaim (BD innovation 2026-10-08) - SHORT, t1s1, 13:00-14:30 ET bar closes.
Short a stock that gapped down >= 0.88% but has climbed back ABOVE today's open by the early afternoon
(the gap-fill rally tends to fade into the close). Found by the stage-2 rework of the owner's RIOT read
(E2 family) + ablation; lineage = gap-down afternoon short (P1-gap_*, failed holdout look 1), so this is
look 2: it needs day-clustered t >= 1.5 on BOTH locked holdouts. Not wired into config.
Train 07-15..08-25: n 4512, +0.066R prod, t_day 1.26 (best day = 64% of total). Valid 08-26..09-15: n 2365,
+0.196R prod, t_day 1.20, ex-best-day +0.157R. ~120-140 qualifying names/day; with a 20/day cap t_day 0.6/1.2.
Educational only - not financial advice."""
import numpy as np

SIDE = "short"
GEOM = "t1s1"
LAYERS = [
    "gap <= -0.88% (opened at least 0.88% below the prior close)",
    "fromOpen > 0 (now trading above today's open)",
    "time window 13:00-14:30 ET (bar close)",
]


def mask(df) -> np.ndarray:
    gap = df["gap"].to_numpy(dtype=float)
    fo = df["fromOpen"].to_numpy(dtype=float)
    tod = df["tod"].to_numpy(dtype=float)
    return (gap <= -0.88) & (fo > 0) & (tod >= 1300) & (tod <= 1430)
