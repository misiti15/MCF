"""swarm1017 rework-cwt14 candidate (Testing-grade only; did NOT reach the lineage bar). Educational only - not
financial advice.

Failed Opening-Range-Low Break Long, deep poke + big gap: 09:50-11:30, price trades >= 0.20 ATR under the 09:30-10:00
low (live from 10:05), the poke bar's volumeRatio < 1, then a close back above the OR low within 3 bars, on a stock
with |gap| >= 2%. Buy at the bar close.
Exit: t1s1 with live scale-out (YAML: scale_out_r 0.5, live_scale_out: true -> bank half at +0.5R, rest to breakeven).
Open history (train 2024-10 + 2025-03..12 / valid 2026-01..10-07, costs in): n 385 / 403, +0.059R / +0.062R, day-t
0.75 / 1.19 (all 1.30) vs lineage bar 5.07; up +0.142 / down +0.076; WF 0.625; ex-top-5-P/L-days -0.016R.
Source: research/swarm1017/rework-cwt14 (stage B, ORL p0.20 k3 v<1 [|gap|>=2] t1s1so 0950-1130).
"""
import numpy as np

import cwt14x_lib as X

SIDE = "long"
GEOM = "t1s1"
LAYERS = ["rework-cwt14 B ORL p0.20 k3 v<1 |gap|>=2 t1s1so 0950-1130"]


def mask(df):
    flag, _, _, x = X.fb(df, "ORL", 0.20, 3, vol=lambda v: v < 1)
    with np.errstate(invalid="ignore"):
        return flag & (np.abs(x.gap) >= 2)
