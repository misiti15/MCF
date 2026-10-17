"""5-minute path simulator and the generalised CWT14 failed-break kernel (PLAN.md). Educational only - not financial advice.

sim(): entry at the signal bar's close, management from the next bar, stop checked first inside a bar, then the
target; breakeven / scale-out / trailing / time-stop updates take effect from the following bar; flat at the
symbol-day's last row (the 15:55 bar). Costs = gates.prod_r: (1c + 1 bps) x tod multiplier on the entry, the exit side
free on target fills, +2c on stop / breakeven fills. Adapted from research/bdi/top5_1015/scan_1015.py `sim`
(adds no-target, trailing).

b3k(): cwt_live_lib.b3 with the reclaim window fixed at kmax and per-signal attributes recorded (bars to reclaim,
poke-bar volumeRatio, max poke depth in ATR, signal ordinal of the day). Filtering ks <= k reproduces kmax = k exactly
(an excursion that has not reclaimed after k bars is not traded in either version and the next inside close resets it).
"""
import numba
import numpy as np


@numba.njit(cache=True)
def _mult(t):
    if t < 935:
        return 3.8
    if t < 950:
        return 2.1
    if t < 1030:
        return 1.4
    return 1.0


@numba.njit(cache=True)
def sim(h, l, c, tod, dend, ent, Rv, side, up, dn, be, so, sof, trr, tra, tsb, tsr):
    n = len(ent)
    r = np.full(n, np.nan, np.float32)
    for q in range(n):
        i = ent[q]
        R = Rv[q]
        if i < 0 or not (R > 0):
            continue
        end = dend[i]
        if end <= i:
            continue
        e = c[i]
        ec = (0.01 + e * 1e-4) * _mult(tod[i])
        stop = e - side * dn * R
        has_t = up > 0
        tgt = e + side * up * R
        spx = e + side * so * R
        scaled = False
        mfe = 0.0
        x = 0.0
        cd = 0
        for k in range(i + 1, end + 1):
            adv = l[k] if side == 1 else h[k]
            fav = h[k] if side == 1 else l[k]
            if side * (adv - stop) <= 0:
                x = stop
                cd = 2
                break
            if has_t and side * (fav - tgt) >= 0:
                x = tgt
                cd = 1
                break
            mfe = max(mfe, side * (fav - e) / R)
            if tsb > 0 and (k - i) >= tsb and mfe < tsr:
                x = c[k]
                cd = 4
                break
            if be > 0 and mfe >= be:
                stop = max(stop, e) if side == 1 else min(stop, e)
            if so > 0 and (not scaled) and side * (fav - spx) >= 0:
                scaled = True
                stop = max(stop, e) if side == 1 else min(stop, e)
            if trr > 0 and mfe >= tra:
                ts = e + side * (mfe - trr) * R
                stop = max(stop, ts) if side == 1 else min(stop, ts)
        if cd == 0:
            x = c[end]
            cd = 6
        xc = 0.0 if cd == 1 else (0.01 + x * 1e-4 + (0.02 if cd == 2 else 0.0))
        g = side * (x - e) / R
        if scaled:
            g = sof * so + (1 - sof) * g
            xc = (1 - sof) * xc
        r[q] = g - (ec + xc) / R
    return r


@numba.njit(cache=True)
def b3k(new, lo_ok, L, h, l, c, vr, atr, p, kmax, upper):
    n = len(c)
    flag = np.zeros(n, np.bool_)
    ks = np.zeros(n, np.int8)
    v0o = np.full(n, np.nan, np.float32)
    dep = np.full(n, np.nan, np.float32)
    ordn = np.zeros(n, np.int16)
    inexc = False
    stale = False
    st = 0
    v0 = np.nan
    dmax = 0.0
    cnt = 0
    for i in range(n):
        if new[i]:
            inexc = False
            stale = False
            cnt = 0
        if not lo_ok[i] or np.isnan(L[i]):
            continue
        if upper:
            beyond = h[i] >= L[i] + p * atr[i]
            inside = c[i] < L[i]
            d = (h[i] - L[i]) / atr[i]
        else:
            beyond = l[i] <= L[i] - p * atr[i]
            inside = c[i] > L[i]
            d = (L[i] - l[i]) / atr[i]
        if (not inexc) and (not stale) and beyond:
            inexc = True
            st = i
            v0 = vr[i]
            dmax = d
        if inexc:
            if d > dmax:
                dmax = d
            if inside:
                if i - st <= kmax:
                    flag[i] = True
                    ks[i] = i - st
                    v0o[i] = v0
                    dep[i] = dmax
                    cnt += 1
                    ordn[i] = cnt
                inexc = False
            elif i - st > kmax:
                inexc = False
                stale = True
        elif stale and inside:
            stale = False
    return flag, ks, v0o, dep, ordn
