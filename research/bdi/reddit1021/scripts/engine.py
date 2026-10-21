"""reddit1021 engine (numba): signals (untouched levels, continuation / reversal 5m candles) + fib-retrace limit
entries + 1-minute exit simulation + same-minute random-day controls. All rules are in PLAN.md.
Educational only - not financial advice."""
from __future__ import annotations

import numpy as np
from numba import njit

SLIP_PS, SLIP_BPS, STOP_EXTRA = 0.01, 1e-4, 0.02
FAM_PRIO = np.array([3, 1, 2, 0], np.int64)   # level pair order in LV: OR, PM, AH, PD ; priority PD, PM, AH, OR, SW
# family codes: 0 OR, 1 PM, 2 AH, 3 PD, 4 SW
PRIO = np.array([3, 1, 2, 0, 4], np.int64)    # PD first ... SW last

# param vector indices
P_TYPE, P_K, P_VOL, P_TREND, P_FRESH, P_FIRST, P_KLO, P_KHI, P_FAMMASK, P_FIB, P_MULT, P_EXIT, P_ENTRY, P_BODY, \
    P_CLOSEZ, P_SIDEONLY = range(16)
NPAR = 16


def params(type_=0, k=1.5, vol=1, trend=0, fresh=1, first=0, klo=3, khi=23, fammask=31, fib=0.5, mult=2.0, exit_=0,
           entry=0, body=0.6, closez=0.35, sideonly=0):
    p = np.zeros(NPAR)
    p[:] = (type_, k, vol, trend, fresh, first, klo, khi, fammask, fib, mult, exit_, entry, body, closez,
            sideonly)
    return p


@njit(cache=True)
def tod_mult(m):
    # m = minute index since 09:30 of the fill bar (bar start); bar-close HHMM thresholds 935 / 950 / 1030
    close = m + 1
    if close < 5:
        return 3.8
    if close < 20:
        return 2.1
    if close < 60:
        return 1.4
    return 1.0


@njit(cache=True)
def exit_sim(o, h, l, c, mn, j0, j1, e, stop, tgt, side, last_min):
    """Walk 1-minute bars j0..j1-1 (positions), from minute after entry; stop first; returns (px, kind, jexit)."""
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
def cost_r(e, px, kind, R, fill_min, tier):
    s_in = (SLIP_PS + e * SLIP_BPS) * tod_mult(fill_min)
    s_out = 0.0 if kind == 2 else (SLIP_PS + px * SLIP_BPS)
    if kind == 1:
        s_out += STOP_EXTRA
    return tier * (s_in + s_out) / R


@njit(cache=True)
def run(P, start, m_o, m_h, m_l, m_c, m_min, LV, tier, elig, fo, fh, fl, fc, fv, fatr, fema, fv20, fvprev, fcprev,
        fvwap, tvwap_above, tema_above):
    """One symbol, one configuration. tvwap_above / tema_above [nd, 78]: trend state (+1 / -1 / 0 unknown) at each
    5m close (own symbol for IDX, SPY for STK). Returns trade rows (float array, columns below)."""
    nd = LV.shape[0]
    out = np.full((nd * 6, 14), np.nan)
    nout = 0
    typ = int(P[0]); kmul = P[1]; volm = int(P[2]); trend = int(P[3]); fresh = int(P[4]); first = int(P[5])
    klo = int(P[6]); khi = int(P[7]); fmask = int(P[8]); fib = P[9]; mult = P[10]; exm = int(P[11]); entm = int(P[12])
    bodyf = P[13]; closez = P[14]; sideonly = int(P[15])
    lv = np.empty(32); lfam = np.empty(32, np.int64); lavail = np.empty(32, np.int64); lused = np.zeros(32, np.bool_)
    for d in range(nd):
        if not elig[d]:
            continue
        a, b = start[d], start[d + 1]
        if b - a < 300:
            continue
        o = m_o[a:b]; h = m_h[a:b]; l = m_l[a:b]; c = m_c[a:b]; mn = m_min[a:b]
        # static levels
        nl = 0
        for q in range(8):
            fam = q // 2
            if np.isfinite(LV[d, q]) and (fmask >> fam) & 1:
                lv[nl] = LV[d, q]; lfam[nl] = fam; lavail[nl] = 3 if fam == 0 else 0; lused[nl] = False
                nl += 1
        busy_until = -1
        nsig = 0
        for k in range(3, 24):
            # swing pivots confirmed by the end of bar k-1 (pivot j, j+2 <= k-1) -> add once
            j = k - 3
            if j >= 2 and (fmask >> 4) & 1 and nl < 30:
                hj = fh[d, j]; lj = fl[d, j]
                if np.isfinite(hj) and hj > fh[d, j - 1] and hj > fh[d, j - 2] and hj > fh[d, j + 1] and hj > fh[d, j + 2]:
                    lv[nl] = hj; lfam[nl] = 4; lavail[nl] = j + 3; lused[nl] = False; nl += 1
                if np.isfinite(lj) and lj < fl[d, j - 1] and lj < fl[d, j - 2] and lj < fl[d, j + 1] and lj < fl[d, j + 2]:
                    lv[nl] = lj; lfam[nl] = 4; lavail[nl] = j + 3; lused[nl] = False; nl += 1
            if k < klo or k > khi:
                continue
            H = fh[d, k]; L = fl[d, k]; C = fc[d, k]; PC = fcprev[d, k]; V = fv[d, k]; A = fatr[d, k]
            if not (np.isfinite(H) and np.isfinite(PC) and np.isfinite(A)) or A <= 0:
                continue
            rng = H - L
            if rng <= 0 or rng < kmul * A:
                continue
            if volm == 1 and not (V > fvprev[d, k]):
                continue
            if volm == 2 and not (V > 1.5 * fvprev[d, k]):
                continue
            if volm == 3 and not (V > fv20[d, k]):
                continue
            side = 0
            bestp = 99
            for q in range(nl):
                if lused[q] or lavail[q] > k:
                    continue
                L0 = lv[q]
                # touch state between availability and k-1
                above = True; below = True
                for kk in range(lavail[q], k):
                    if np.isfinite(fh[d, kk]):
                        if fh[d, kk] >= L0:
                            above = False
                        if fl[d, kk] <= L0:
                            below = False
                if fresh == 0:
                    above = PC < L0
                    below = PC > L0
                s = 0
                if typ == 0:   # continuation
                    if abs(C - PC) >= bodyf * rng:
                        if above and C > L0 and C > PC:
                            s = 1
                        elif below and C < L0 and C < PC:
                            s = -1
                else:          # reversal
                    if above and H > L0 and C < L0 and C <= L + closez * rng:
                        s = -1
                    elif below and L < L0 and C > L0 and C >= H - closez * rng:
                        s = 1
                if s != 0:
                    if side == 0 or PRIO[lfam[q]] < bestp:
                        if side == 0 or s == side:
                            side = s; bestp = PRIO[lfam[q]]
            if side == 0:
                continue
            fam_out = -1
            for f in range(5):
                if PRIO[f] == bestp:
                    fam_out = f
            # consume every level this candle crossed / wicked (one trade per level)
            for q in range(nl):
                if lavail[q] <= k and L <= lv[q] <= H:
                    lused[q] = True
            if trend == 1 and tvwap_above[d, k] != side:
                continue
            if trend == 2 and tema_above[d, k] != side:
                continue
            if sideonly != 0 and side != sideonly:
                continue
            m_close = 5 * (k + 1)
            if m_close < busy_until:
                continue
            if first == 1 and nsig > 0:
                continue
            nsig += 1
            buf = max(0.01, 0.02 * rng)
            stop = L - buf if side > 0 else H + buf
            E = H - fib * rng if side > 0 else L + fib * rng
            # locate first 1-minute bar at / after m_close
            p0 = 0
            while p0 < len(mn) and mn[p0] < m_close:
                p0 += 1
            if p0 >= len(mn):
                continue
            jf = -1
            efill = E
            if entm == 0 or entm == 1:
                p = p0
                while p < len(mn) and mn[p] < m_close + 10:
                    if side > 0:
                        hit = l[p] < E if entm == 0 else l[p] <= E
                    else:
                        hit = h[p] > E if entm == 0 else h[p] >= E
                    if hit:
                        jf = p
                        break
                    p += 1
                if jf < 0:
                    busy_until = m_close + 10
                    continue
            elif entm == 2:
                efill = C
                jf = p0 - 1     # entered at the candle close; exits from p0
            else:              # lab-runnable: close of the first next 5m bar that trades through the fib
                for kk in (k + 1, k + 2):
                    if kk < 78 and np.isfinite(fl[d, kk]):
                        if (side > 0 and fl[d, kk] < E) or (side < 0 and fh[d, kk] > E):
                            efill = fc[d, kk]
                            mend = 5 * (kk + 1)
                            p = p0
                            while p < len(mn) and mn[p] < mend:
                                p += 1
                            jf = p - 1
                            break
                if jf < 0:
                    if first != 2:
                        busy_until = m_close + 10
                    continue
                if side * (efill - stop) <= 1e-6 * efill:      # zero risk (incl. floating-point noise): no trade
                    if first != 2:
                        busy_until = m_close + 10
                    continue
            R = side * (efill - stop)
            if R <= 1e-6 * efill:
                continue
            tgt = efill + side * mult * R
            last = 384 if exm == 0 else max(119, mn[jf] + 10)
            if entm <= 1 and ((side > 0 and l[jf] <= stop) or (side < 0 and h[jf] >= stop)):
                px = stop; kind = 1; jx = jf
            else:
                px, kind, jx = exit_sim(o, h, l, c, mn, jf + 1, len(mn), efill, stop, tgt, side, last)
                if kind < 0:
                    continue
            fill_min = mn[jf] if entm <= 1 else (m_close - 1 if entm == 2 else mn[jf])
            gross = side * (px - efill) / R
            cst = cost_r(efill, px, kind, R, fill_min, tier[d])
            busy_until = mn[jx] + 1
            out[nout, 0] = d; out[nout, 1] = k; out[nout, 2] = side; out[nout, 3] = fam_out
            out[nout, 4] = gross - cst; out[nout, 5] = gross; out[nout, 6] = kind; out[nout, 7] = fill_min
            out[nout, 8] = R / efill; out[nout, 9] = efill; out[nout, 10] = mn[jx]; out[nout, 11] = cst
            out[nout, 12] = tier[d]; out[nout, 13] = rng / A
            nout += 1
            if nout >= out.shape[0]:
                return out[:nout]
            if first == 2:      # module semantics (LabStrategy, refire off): first filled trade of the day only
                break
    return out[:nout]


@njit(cache=True)
def control(trades, days_pick, start, m_o, m_h, m_l, m_c, m_min, tier, mult, exm):
    """Random-day same-minute control. For trade t, days_pick[t, :] lists other sessions (-1 = none): market entry at
    the close of the fill minute, same side, same R/price, same target multiple and exit rule. Mean net R per trade."""
    nt = trades.shape[0]
    res = np.full(nt, np.nan)
    for t in range(nt):
        side = trades[t, 2]; fm = trades[t, 7]; rf = trades[t, 8]
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
            last = 384 if exm == 0 else max(119, fm + 10)
            px, kind, jx = exit_sim(m_o[a:b], m_h[a:b], m_l[a:b], m_c[a:b], mn, p + 1, len(mn), e, stop, tgt, side, last)
            if kind < 0:
                continue
            tot += side * (px - e) / R - cost_r(e, px, kind, R, fm, tier[d])
            n += 1
        if n:
            res[t] = tot / n
    return res
