"""swing1022 engine (numba): 15-minute swing-level break-and-retest / Nth-rejection signals, POI targets, 1-minute exit
simulation, same-minute random-day controls. All rules are in PLAN.md. Educational only - not financial advice."""
from __future__ import annotations

import numpy as np
from numba import njit

SLIP_PS, SLIP_BPS, STOP_EXTRA = 0.01, 1e-4, 0.02
NB = 26
NPOI_MAX = 128

(P_TYPE, P_TOL, P_M, P_NREJ, P_REJMODE, P_ENTRY, P_TMODE, P_TMULT, P_SBUF, P_KHI, P_VOL, P_TREND, P_SIDE, P_FRESH,
 P_CHOCH, P_LEVPD, P_LEVRN, P_LEVSW, P_N) = range(19)
NPAR = 19
DEFAULT = dict(type_=0, tol=0.1, m=4, nrej=3, rejmode=0, entry=0, tmode=0, tmult=2.0, sbuf=0.1, khi=7, vol=0.0,
               trend=0, side=0, fresh=0, choch=0, levpd=0, levrn=0, levsw=0, n=2)
KEYS = list(DEFAULT)


def params(**kw):
    d = dict(DEFAULT)
    for k in kw:
        if k not in d:
            raise KeyError(k)
    d.update(kw)
    return np.array([float(d[k]) for k in KEYS])


@njit(cache=True)
def tod_mult(m):
    close = m + 1
    if close < 5:
        return 3.8
    if close < 20:
        return 2.1
    if close < 60:
        return 1.4
    return 1.0


@njit(cache=True)
def cost_r(e, px, kind, R, fill_min, tier):
    s_in = (SLIP_PS + e * SLIP_BPS) * tod_mult(fill_min)
    s_out = 0.0 if kind == 2 else (SLIP_PS + px * SLIP_BPS)
    if kind == 1:
        s_out += STOP_EXTRA
    return tier * (s_in + s_out) / R


@njit(cache=True)
def exit_sim(o, h, l, c, mn, j0, j1, stop, tgt, side, last_min):
    j = j0
    while j < j1 and mn[j] <= last_min:
        if side > 0:
            if o[j] <= stop:
                return o[j], 1, j
            if l[j] <= stop:
                return stop, 1, j
            if h[j] >= tgt:
                return tgt, 2, j
        else:
            if o[j] >= stop:
                return o[j], 1, j
            if h[j] >= stop:
                return stop, 1, j
            if l[j] <= tgt:
                return tgt, 2, j
        j += 1
    jj = j - 1
    if jj < j0:
        return np.nan, -1, jj
    return c[jj], 0, jj


@njit(cache=True)
def target_of(e, s, R, a, tmode, tmult, poi, npoi, step):
    """Target price (nan = skip). poi[:npoi] = POI prices (swings, PD, PM ...); round numbers from `step`."""
    if tmode == 1:
        return e + s * tmult * R
    mind = 0.1 * a
    best_next = 1e18
    best_first = 1e18
    for i in range(npoi):
        x = poi[i]
        if not np.isfinite(x):
            continue
        dd = s * (x - e)
        if dd >= mind:
            if dd < best_next:
                best_next = dd
            if dd >= tmult * R and dd < best_first:
                best_first = dd
    if np.isfinite(step) and step > 0:
        if s > 0:
            r1 = np.ceil((e + mind) / step) * step
            r2 = np.ceil((e + max(mind, tmult * R)) / step) * step
        else:
            r1 = np.floor((e - mind) / step) * step
            r2 = np.floor((e - max(mind, tmult * R)) / step) * step
        d1 = s * (r1 - e); d2 = s * (r2 - e)
        if d1 >= mind and d1 < best_next:
            best_next = d1
        if d2 >= tmult * R and d2 < best_first:
            best_first = d2
    if tmode == 0:
        if best_next >= 1e17 or best_next < tmult * R:
            return np.nan
        return e + s * best_next
    if best_first >= 1e17:
        return np.nan
    return e + s * best_first


@njit(cache=True)
def run(P, start, m_o, m_h, m_l, m_c, m_min, fo, fh, fl, fc, fv, fatr, fv20, SH, SL, CH, FR, POI, PD, PM, step,
        tier, elig, tv, to):
    """One symbol, one configuration. tv / to [nd, 26]: SPY's close vs its session VWAP / vs its open (+1 / -1 / 0)
    at each 15m close. Returns trade rows."""
    typ = int(P[P_TYPE]); tolm = P[P_TOL]; M = int(P[P_M]); nrej = int(P[P_NREJ]); rejmode = int(P[P_REJMODE])
    entm = int(P[P_ENTRY]); tmode = int(P[P_TMODE]); tmult = P[P_TMULT]; sbuf = P[P_SBUF]; khi = int(P[P_KHI])
    volx = P[P_VOL]; trend = int(P[P_TREND]); sideonly = int(P[P_SIDE]); fresh = int(P[P_FRESH])
    choch = int(P[P_CHOCH]); levpd = int(P[P_LEVPD]); levrn = int(P[P_LEVRN]); levsw = int(P[P_LEVSW])
    N = int(P[P_N])
    nd = SH.shape[0]
    out = np.full((nd * 8, 16), np.nan)
    nout = 0
    ML = 48
    lv = np.empty(ML); ldir = np.zeros(ML, np.int64); lch = np.zeros(ML, np.int64); lfr = np.zeros(ML, np.int64)
    lav = np.zeros(ML, np.int64); lkind = np.zeros(ML, np.int64)
    st = np.zeros(ML, np.int64); bk = np.zeros(ML, np.int64); bs = np.zeros(ML, np.int64)
    rc_up = np.zeros(ML, np.int64); rc_dn = np.zeros(ML, np.int64)
    poi = np.empty(NPOI_MAX)
    for d in range(nd):
        if not elig[d]:
            continue
        a0, b0 = start[d], start[d + 1]
        if b0 - a0 < 300:
            continue
        o = m_o[a0:b0]; h = m_h[a0:b0]; l = m_l[a0:b0]; c = m_c[a0:b0]; mn = m_min[a0:b0]
        H = fh[d]; L_ = fl[d]; C = fc[d]; V = fv[d]; A = fatr[d]; V20 = fv20[d]
        nl = 0
        if np.isfinite(SH[d]):
            lv[nl] = SH[d]; ldir[nl] = 1; lch[nl] = CH[d, 0]; lfr[nl] = FR[d, 0]; lav[nl] = 1; lkind[nl] = 0; nl += 1
        if np.isfinite(SL[d]):
            lv[nl] = SL[d]; ldir[nl] = 2; lch[nl] = CH[d, 1]; lfr[nl] = FR[d, 1]; lav[nl] = 1; lkind[nl] = 0; nl += 1
        if levpd == 1:
            for q in range(2):
                if np.isfinite(PD[d, q]):
                    lv[nl] = PD[d, q]; ldir[nl] = 3; lch[nl] = -1; lfr[nl] = 1; lav[nl] = 1; lkind[nl] = 1; nl += 1
        if levrn == 1 and np.isfinite(step[d]) and np.isfinite(C[0]):
            base = np.round(C[0] / step[d]) * step[d]
            for q in range(-3, 4):
                lv[nl] = base + q * step[d]; ldir[nl] = 3; lch[nl] = -1; lfr[nl] = 1; lav[nl] = 1; lkind[nl] = 2
                nl += 1
        for q in range(nl):
            st[q] = 0; rc_up[q] = 0; rc_dn[q] = 0
        # base POI list (pre-open swings, PD, PM)
        npoi = 0
        for q in range(POI.shape[1]):
            if np.isfinite(POI[d, q]):
                poi[npoi] = POI[d, q]; npoi += 1
        for q in range(2):
            if np.isfinite(PD[d, q]):
                poi[npoi] = PD[d, q]; npoi += 1
            if np.isfinite(PM[d, q]):
                poi[npoi] = PM[d, q]; npoi += 1
        busy_until = -1
        for k in range(1, NB):
            # today's 15m pivots confirmed at the end of bar k-1 (pivot j = k-1-N, j >= 1: the first candle excluded)
            j = k - 1 - N
            if j >= 1 and j - N >= 0:
                ph = True; pl = True
                for u in range(j - N, j + N + 1):
                    if u == j:
                        continue
                    if not (H[j] > H[u]):
                        ph = False
                    if not (L_[j] < L_[u]):
                        pl = False
                if ph and np.isfinite(H[j]):
                    if npoi < NPOI_MAX:
                        poi[npoi] = H[j]; npoi += 1
                    if levsw == 1 and nl < ML:
                        lv[nl] = H[j]; ldir[nl] = 1; lch[nl] = -1; lfr[nl] = 1; lav[nl] = k; lkind[nl] = 3
                        st[nl] = 0; rc_up[nl] = 0; rc_dn[nl] = 0; nl += 1
                if pl and np.isfinite(L_[j]):
                    if npoi < NPOI_MAX:
                        poi[npoi] = L_[j]; npoi += 1
                    if levsw == 1 and nl < ML:
                        lv[nl] = L_[j]; ldir[nl] = 2; lch[nl] = -1; lfr[nl] = 1; lav[nl] = k; lkind[nl] = 3
                        st[nl] = 0; rc_up[nl] = 0; rc_dn[nl] = 0; nl += 1
            if not (np.isfinite(C[k]) and np.isfinite(C[k - 1]) and np.isfinite(A[k])) or A[k] <= 0:
                continue
            a = A[k]
            # candidate entry at this candle: (side, stop, entry kind 0 close / 1 limit, limit px, order end minute)
            c_side = 0; c_stop = np.nan; c_lim = np.nan; c_end = 0; c_q = -1
            for q in range(nl):
                if lav[q] > k or st[q] == 2:
                    continue
                Lq = lv[q]
                if typ == 0:
                    if st[q] == 1:
                        s = bs[q]
                        if k > bk[q] + M:
                            st[q] = 2
                            continue
                        if s * (C[k] - Lq) < 0:
                            st[q] = 2
                            continue
                        tol = tolm * a
                        if (s > 0 and L_[k] <= Lq + tol and C[k] > Lq) or (s < 0 and H[k] >= Lq - tol and C[k] < Lq):
                            st[q] = 2
                            if c_side == 0:
                                ext = min(L_[k], Lq) if s > 0 else max(H[k], Lq)
                                c_side = s; c_stop = ext - s * max(0.01, sbuf * a); c_q = q
                        continue
                    s = 0
                    if (ldir[q] & 1) and C[k - 1] <= Lq and C[k] > Lq:
                        s = 1
                    elif (ldir[q] & 2) and C[k - 1] >= Lq and C[k] < Lq:
                        s = -1
                    if s == 0:
                        continue
                    st[q] = 2          # consumed unless armed below
                    if fresh == 1:
                        okf = True
                        for u in range(0, k):
                            if (s > 0 and H[u] >= Lq) or (s < 0 and L_[u] <= Lq):
                                okf = False
                        if not okf:
                            continue
                    if choch == 1 and lch[q] != 1:
                        continue
                    if choch == 2 and lch[q] != 0:
                        continue
                    if volx > 0 and not (V[k] > volx * V20[k]):
                        continue
                    if entm == 1:
                        if c_side == 0:
                            tol = tolm * a
                            c_side = s; c_lim = Lq + s * tol; c_stop = Lq - s * max(0.01, sbuf * a)
                            c_end = 15 * (k + 1 + M); c_q = q
                        continue
                    st[q] = 1; bk[q] = k; bs[q] = s
                else:
                    # rejection counting; side decided by where the previous close sits
                    if C[k - 1] < Lq and (ldir[q] & 1):        # resistance: wick above, close back below -> short
                        if C[k] > Lq:
                            st[q] = 2
                            continue
                        if rejmode == 0:
                            rej = H[k] > Lq and C[k] < Lq
                        elif rejmode == 1:
                            rej = H[k] >= Lq - 0.1 * a and C[k] < Lq
                        else:
                            rej = H[k] > Lq + 0.1 * a and C[k] < Lq
                        if not rej:
                            continue
                        rc_up[q] += 1
                        cnt = rc_up[q]; s = -1
                    elif C[k - 1] > Lq and (ldir[q] & 2):      # support: wick below, close back above -> long
                        if C[k] < Lq:
                            st[q] = 2
                            continue
                        if rejmode == 0:
                            rej = L_[k] < Lq and C[k] > Lq
                        elif rejmode == 1:
                            rej = L_[k] <= Lq + 0.1 * a and C[k] > Lq
                        else:
                            rej = L_[k] < Lq - 0.1 * a and C[k] > Lq
                        if not rej:
                            continue
                        rc_dn[q] += 1
                        cnt = rc_dn[q]; s = 1
                    else:
                        continue
                    if entm == 1:
                        if cnt == nrej - 1:
                            st[q] = 2
                            if fresh == 1 and lfr[q] != 1:
                                continue
                            if choch == 1 and lch[q] != 1:
                                continue
                            if choch == 2 and lch[q] != 0:
                                continue
                            if c_side == 0:
                                c_side = s; c_lim = Lq; c_stop = Lq - s * max(0.01, sbuf * a)
                                c_end = 15 * (khi + 1); c_q = q
                        continue
                    if cnt < nrej:
                        continue
                    st[q] = 2
                    if fresh == 1 and lfr[q] != 1:
                        continue
                    if choch == 1 and lch[q] != 1:
                        continue
                    if choch == 2 and lch[q] != 0:
                        continue
                    if volx > 0 and not (V[k] > volx * V20[k]):
                        continue
                    if c_side == 0:
                        ext = H[k] if s < 0 else L_[k]
                        c_side = s; c_stop = ext - s * max(0.01, sbuf * a); c_q = q
            if c_side == 0:
                continue
            s = c_side
            if entm == 0 and k > khi:
                continue
            if entm == 1 and k > khi:
                continue
            if sideonly != 0 and s != sideonly:
                continue
            if trend == 1 and tv[d, k] != s:
                continue
            if trend == 2 and to[d, k] != s:
                continue
            m_close = 15 * (k + 1)
            if m_close < busy_until:
                continue
            p0 = 0
            while p0 < len(mn) and mn[p0] < m_close:
                p0 += 1
            if p0 >= len(mn):
                continue
            if entm == 0:
                e = C[k]
                jf = p0 - 1
                fill_min = m_close - 1
            else:
                e = c_lim
                jf = -1
                p = p0
                while p < len(mn) and mn[p] < c_end:
                    if (s > 0 and l[p] < e) or (s < 0 and h[p] > e):
                        jf = p
                        break
                    p += 1
                if jf < 0:
                    busy_until = c_end
                    continue
                fill_min = mn[jf]
            R = s * (e - c_stop)
            if R <= 1e-6 * e:
                continue
            tgt = target_of(e, s, R, a, tmode, tmult, poi, npoi, step[d])
            if not np.isfinite(tgt):
                continue
            if entm == 1 and ((s > 0 and l[jf] <= c_stop) or (s < 0 and h[jf] >= c_stop)):
                px = c_stop; kind = 1; jx = jf
            else:
                px, kind, jx = exit_sim(o, h, l, c, mn, jf + 1, len(mn), c_stop, tgt, s, 384)
                if kind < 0:
                    continue
            gross = s * (px - e) / R
            cst = cost_r(e, px, kind, R, fill_min, tier[d])
            busy_until = mn[jx] + 1
            out[nout, 0] = d; out[nout, 1] = k; out[nout, 2] = s; out[nout, 3] = lkind[c_q]
            out[nout, 4] = gross - cst; out[nout, 5] = gross; out[nout, 6] = kind; out[nout, 7] = fill_min
            out[nout, 8] = R / e; out[nout, 9] = e; out[nout, 10] = mn[jx]; out[nout, 11] = cst
            out[nout, 12] = tier[d]; out[nout, 13] = s * (tgt - e) / R; out[nout, 14] = lch[c_q]; out[nout, 15] = c_stop
            nout += 1
            if nout >= out.shape[0]:
                return out[:nout]
    return out[:nout]



@njit(cache=True)
def control(trades, days_pick, start, m_o, m_h, m_l, m_c, m_min, tier):
    """Random-day same-minute control: market entry at the close of the trade's fill minute on other sessions, same
    side, same R / price, the trade's own target multiple (col 13), flat 15:55. Mean net R per trade."""
    nt = trades.shape[0]
    res = np.full(nt, np.nan)
    for t in range(nt):
        side = trades[t, 2]; fm = trades[t, 7]; rf = trades[t, 8]; mult = trades[t, 13]
        tot = 0.0; n = 0
        for u in range(days_pick.shape[1]):
            d = days_pick[t, u]
            if d < 0:
                continue
            a, b = start[d], start[d + 1]
            mn = m_min[a:b]
            p = 0
            while p < len(mn) and mn[p] < fm:
                p += 1
            if p >= len(mn) or mn[p] != fm:
                continue
            e = m_c[a + p]
            R = rf * e
            stop = e - side * R
            tgt = e + side * mult * R
            px, kind, jx = exit_sim(m_o[a:b], m_h[a:b], m_l[a:b], m_c[a:b], mn, p + 1, len(mn), stop, tgt, side, 384)
            if kind < 0:
                continue
            tot += side * (px - e) / R - cost_r(e, px, kind, R, fm, tier[d])
            n += 1
        if n:
            res[t] = tot / n
    return res
