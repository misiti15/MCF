"""swarm1017 rework-cwt14 candidate (Testing-grade only; did NOT reach the lineage bar). Educational only - not
financial advice.

Failed Opening-Range-Low Break Long on a gap-up name that has cooled: 09:50-15:00, price trades >= 0.10 ATR under the
09:30-10:00 low (live from 10:05), then a close back above it within 3 bars, with gap > 0 and heat <= -30 at the bar.
Exit: t05s1 with live scale-out (YAML: scale_out_r 0.25, live_scale_out: true).
Open history (train / valid, costs in): n 254 / 368, +0.039R / +0.028R, day-t 1.01 / 0.62 (all 1.05) vs bar 5.07;
up +0.036 / down +0.032; WF 0.75; ex-top-5-P/L-days +0.001R.
Source: research/swarm1017/rework-cwt14 (stage C, ORL p0.10 k3 any [gap>0+heat<=-30] t05s1so 0950-1500).
"""
import numpy as np

import cwt14x_lib as X

SIDE = "long"
GEOM = "t05s1"
LAYERS = ["rework-cwt14 C ORL p0.10 k3 any gap>0+heat<=-30 t05s1so 0950-1500"]


def mask(df):
    flag, _, _, x = X.fb(df, "ORL", 0.10, 3)
    with np.errstate(invalid="ignore"):
        return flag & (x.gap > 0) & (df["heat"].to_numpy(float) <= -30)
