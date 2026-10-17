"""swarm1017 rework-cwt14 candidate (Testing-grade only; did NOT reach the lineage bar). Educational only - not
financial advice.

Failed Prior-Day-Low Break Long on a weak tape, stock up on the day: 09:50-15:00, price trades >= 0.05 ATR under
yesterday's low, poke-bar volumeRatio < 1, then a close back above it within 3 bars, while the stock is > +1% from its
open and fewer than 40% of the adv >= $95M universe are above their open (breadth).
**Live code needed:** breadth is not in the LabStrategy frame; the runner must add a `breadth` column (share of the
95M universe above its open at the bar close). Without it the mask is all False.
Exit: t05s1 with live scale-out (YAML: scale_out_r 0.25, live_scale_out: true).
Open history (train / valid, costs in): n 199 / 239, +0.022R / +0.055R, day-t 0.46 / 1.24 (all 1.24) vs bar 5.07;
up +0.161 / down +0.028; WF 0.70; ex-top-5-P/L-days -0.003R.
Source: research/swarm1017/rework-cwt14 (stage C, PDL p0.05 k3 v<1 [brd<.4+fo>1] t05s1so 0950-1500).
"""
import numpy as np

import cwt14x_lib as X

SIDE = "long"
GEOM = "t05s1"
LAYERS = ["rework-cwt14 C PDL p0.05 k3 v<1 brd<.4+fo>1 t05s1so 0950-1500"]


def mask(df):
    if "breadth" not in df.columns:
        return np.zeros(len(df), bool)
    flag, _, _, _ = X.fb(df, "PDL", 0.05, 3, vol=lambda v: v < 1)
    with np.errstate(invalid="ignore"):
        return flag & (df["breadth"].to_numpy(float) < 0.4) & (df["fromOpen"].to_numpy(float) > 1)
