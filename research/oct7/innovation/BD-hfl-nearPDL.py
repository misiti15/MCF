"""BD-hfl-nearPDL (BD innovation 2026-10-08) - LONG, t1s1, 11:05-13:30 ET bar closes.
heat_fade_long (research/heat/candidates/regime_5.py) taken only when the close is below, or within
0.25 daily ATR above, the PRIOR-DAY LOW (a capitulation fade into a support level). Rework of a live
setup (heat_fade_long lineage). The autopsy's hfl_deep4 is a competing rework of the same lineage:
only ONE of them should take the next holdout look (look 2, t >= 1.5 on both holdouts).
Parent: train n 1595 +0.069R t 0.57 / valid n 461 +0.060R t 1.83.
This: train n 1128 +0.109R prod, t_day 1.14, ex-best +0.078R / valid n 365 +0.075R, t_day 2.05, ex-best +0.049R.
Educational only - not financial advice."""
import os
import sys

import numpy as np

_here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(_here, "..", "..", "heat", "candidates")))
import regime_5  # noqa: E402

SIDE = "long"
GEOM = "t1s1"
LAYERS = [
    "heat_fade_long (regime_5 score >= 57.5; gap-up names, 11:05-13:30)",
    "dist_pdl_atr < 0.25 (close below or within 0.25 daily ATR above the prior-day low)",
]


def mask(df) -> np.ndarray:
    s = regime_5.score(df)
    pdl = df["dist_pdl_atr"].to_numpy(dtype=float)
    return (np.nan_to_num(s, nan=-1e9) >= regime_5.LONG_AT) & (pdl < 0.25)
