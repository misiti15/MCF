"""Generalised numba ports of the CWT kernels in research/bdi/cwt/live/cwt_live_lib.py (PLAN.md).
At the parent parameters each kernel reproduces cwt_live_lib exactly (checked by parity.py). Inputs are the arrays of
cwt_live_lib.arrays(df) on the live-like frame (09:35 rows onward). Educational only - not financial advice."""
import numba
import numpy as np


@numba.njit(cache=True)
def b1k(new, c, h, l, vwap, open_d, atr, a, dthr, trig):
    """cwt_live_lib.b1 with the drop threshold (0.4) as a parameter."""
    n = len(c)
    flag = np.zeros(n, np.bool_)
    hod = -1e18
    bd = False
    bdrow = -1
    bdhi = -1e18
    Lmin = 1e18
    Bmax = -1e18
    for i in range(n):
        if new[i]:
            hod = -1e18
            bd = False
            bdhi = -1e18
            Lmin = 1e18
            Bmax = -1e18
        if h[i] > hod:
            hod = h[i]
            bd = False
            Lmin = 1e18
            Bmax = -1e18
            continue
        if bd:
            bdhi = max(bdhi, h[i])
            if i > bdrow:
                ok = False
                if trig == 1:
                    ok = h[i] >= vwap[i] - 0.05 * atr[i] and c[i] < vwap[i]
                elif Lmin < 1e17 and Bmax > -1e17 and hod > Lmin:
                    rt = (Bmax - Lmin) / (hod - Lmin)
                    ok = 0.38 <= rt <= 0.62 and c[i] < l[i - 1]
                if ok and bdhi > c[i]:
                    flag[i] = True
        if l[i] < Lmin:
            Lmin = l[i]
            Bmax = -1e18
        else:
            Bmax = max(Bmax, h[i])
        if (not bd) and atr[i] > 0 and hod > open_d[i]:
            run = (hod - open_d[i]) / atr[i]
            drop = (hod - c[i]) / (hod - open_d[i])
            if run >= a and drop >= dthr and c[i] < vwap[i]:
                bd = True
                bdrow = i
                bdhi = h[i]
    return flag


@numba.njit(cache=True)
def b4ak(new, c, h, l, hod, atr, nco):
    """cwt_live_lib.b4a with the touch count recorded (flag needs >= 2 touches; parent = >= 3). Returns touches
    (0 = no signal)."""
    n = len(c)
    out = np.zeros(n, np.int16)
    s0 = 0
    for i in range(n):
        if new[i]:
            s0 = i
        if i - s0 + 1 < nco + 6:
            continue
        thr = hod[i] - 0.1 * atr[i]
        touches = 0
        for k in range(s0, i + 1):
            if h[k] >= thr:
                touches += 1
        if touches < 2:
            continue
        a = i - nco + 1
        m0 = max(s0, a - 20)
        mr = 0.0
        for k in range(m0, a):
            mr += h[k] - l[k]
        mr = mr / (a - m0)
        ok = True
        lo = 1e18
        for k in range(a, i + 1):
            if not (h[k] - l[k] < 0.5 * mr and c[k] <= hod[i] and hod[i] - c[k] <= 0.25 * atr[i]):
                ok = False
                break
            lo = min(lo, l[k])
        if ok and lo < c[i]:
            out[i] = min(touches, 30000)
    return out


@numba.njit(cache=True)
def b4bk(new, c, h, l, vwap, open_d, atr):
    """cwt_live_lib.b4b with s and the pullback band free: returns push (ATR) and pullback depth d at every breakout
    bar that has the parent's other conditions (NaN elsewhere). Parent: push >= 1.0 and 0.3 <= d <= 0.5."""
    n = len(c)
    push = np.full(n, np.nan)
    dep = np.full(n, np.nan)
    hod = -1e18
    L = 1e18
    above = True
    nb = 0
    for i in range(n):
        if new[i]:
            hod = -1e18
            L = 1e18
            above = True
            nb = 0
        if nb > 0 and hod > open_d[i] and atr[i] > 0 and above and c[i] > hod:
            d = (hod - L) / (hod - open_d[i])
            if L < c[i]:
                push[i] = (hod - open_d[i]) / atr[i]
                dep[i] = d
        if h[i] > hod:
            hod = h[i]
            L = 1e18
            above = True
            nb = 0
        else:
            L = min(L, l[i])
            above = above and l[i] > vwap[i]
            nb += 1
    return push, dep


@numba.njit(cache=True)
def b5k(new, c, h, c6, lodp, vc3, atr, m, v):
    """cwt_live_lib.b5 (c6 = close 6 bars back, lodp = prior bar's LOD with NaN -> -1e18, vc3 = max vol_climax of the
    last 3 bars with NaN -> 0)."""
    n = len(c)
    flag = np.zeros(n, np.bool_)
    fl = False
    for i in range(n):
        if new[i]:
            fl = False
        if fl and i > 0 and (not new[i]) and c[i] > h[i - 1]:
            flag[i] = True
        if (not fl) and atr[i] > 0 and (not np.isnan(c6[i])) and (c6[i] - c[i]) >= m * atr[i] and c[i] < lodp[i] \
                and vc3[i] >= v:
            fl = True
    return flag
