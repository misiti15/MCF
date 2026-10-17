"""Live-frame port of the CWT14 rework kernel (research/swarm1017/rework-cwt14/sim.py b3k). Educational only - not
financial advice.

Same session state as research/bdi/cwt/live/cwt_live_lib.b3 (arrays() over every bar of the day from 09:35, the
volumeRatio blanked before 09:50 as scored): an excursion starts on the first bar trading >= p ATR beyond the level
after a close inside; the signal is a close back inside within k bars of that start. Knobs: k, a poke-bar volume
condition, and the poke depth (max excursion in ATR up to the signal bar). Only information known at the bar close.
"""
from __future__ import annotations

import math
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "bdi", "cwt", "live"))
import cwt_live_lib as CL  # noqa: E402

NAN = float("nan")


def fb(df, level: str, p: float, k: int = 3, vol=None, upper: bool | None = None):
    """Returns (flag, v0, depth) arrays. level PDL / PDH / ORL / ORH; vol None or a callable on the poke-bar
    volumeRatio (NaN -> False)."""
    x = CL.arrays(df)
    up = level in ("PDH", "ORH") if upper is None else upper
    if level in ("PDL", "PDH"):
        L = x.pdh if up else x.pdl
        lo_ok = np.ones(x.n, bool)
    else:
        at10 = np.where(x.tod == 1000, x.hod if up else x.lod, NAN)
        L = pd.Series(at10).groupby(x.seg).ffill().to_numpy(float)
        lo_ok = x.tod >= 1005
    c, h, l, vr, atr, new = x.c, x.h, x.l, x.vr, x.atr, x.new
    flag = np.zeros(x.n, bool)
    v0o = np.full(x.n, NAN)
    dep = np.full(x.n, NAN)
    inexc = stale = False
    st, v0, dmax = 0, NAN, 0.0
    for i in range(x.n):
        if new[i]:
            inexc = stale = False
        if not lo_ok[i] or math.isnan(L[i]):
            continue
        beyond = (h[i] >= L[i] + p * atr[i]) if up else (l[i] <= L[i] - p * atr[i])
        inside = (c[i] < L[i]) if up else (c[i] > L[i])
        d = ((h[i] - L[i]) if up else (L[i] - l[i])) / atr[i]
        if not inexc and not stale and beyond:
            inexc, st, v0, dmax = True, i, vr[i], d
        if inexc:
            dmax = max(dmax, d)
            if inside:
                if i - st <= k:
                    ok = True
                    if vol is not None:
                        ok = (not math.isnan(v0)) and bool(vol(v0))
                    if ok:
                        flag[i] = True
                        v0o[i], dep[i] = v0, dmax
                inexc = False
            elif i - st > k:
                inexc = False
                stale = True
        elif stale and inside:
            stale = False
    return flag, v0o, dep, x
