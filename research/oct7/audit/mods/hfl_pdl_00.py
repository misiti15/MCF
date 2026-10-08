"""AUDIT plateau neighbour of BD-hfl-nearPDL: dist_pdl_atr < 0.0. Educational only - not financial advice."""
import os, sys
import numpy as np
sys.path.insert(0, os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "heat", "candidates")))
import regime_5  # noqa: E402
SIDE, GEOM = "long", "t1s1"


def mask(df):
    s = regime_5.score(df)
    return (np.nan_to_num(s, nan=-1e9) >= regime_5.LONG_AT) & (df["dist_pdl_atr"].to_numpy(dtype=float) < 0.0)
