"""IDXHEDGE-1127: E4 minute book engine (research/cfprimary_1127/e4nb.py sim_day, unchanged logic) that also records, per
minute bar (index m - 570), the book's closed + open R (TB), the net beta exposure E (R per +1% SPY) and E by setup.
Daily R by setup is asserted equal to e4nb.run on every day by ih_run.py. Educational only - not financial advice."""
import numpy as np
from numba import njit, prange

N = 4


@njit(cache=True)
def sim_day(a, b, si, sym, side, ent, risk, lc, em, xm, rr, off, n, bb, lo, path, outR, TB, EE, ES):
    realized = np.zeros(N)
    latched = np.zeros(N, np.bool_); olat = np.zeros(N, np.bool_)
    cnt = np.zeros(N, np.int64)
    nsym = 0
    for k in range(a, b):
        if sym[k] + 1 > nsym:
            nsym = sym[k] + 1
    symcnt = np.zeros((N, nsym + 1), np.int64)
    entm = np.zeros((N, 1000), np.int64)
    opn = np.empty(b - a, np.int64); no = 0
    m0 = 10 ** 9; last = -1
    for k in range(a, b):
        if em[k] < m0:
            m0 = em[k]
        if em[k] > last:
            last = em[k]
    if last < 0:
        return
    halted = False
    p = a
    mlast = m0
    for m in range(m0, 956):
        if m > last and no == 0:
            break
        mlast = m
        q = 0
        for i in range(no):
            k = opn[i]
            if xm[k] <= m:
                realized[si[k]] += rr[k]; cnt[si[k]] -= 1; symcnt[si[k], sym[k]] -= 1
            else:
                opn[q] = k; q += 1
        no = q
        for s in range(N):
            if realized[s] <= -2.0 + 1e-12:
                latched[s] = True
        while p < b and em[p] < m:
            p += 1
        while p < b and em[p] == m:
            k = p; p += 1
            s = si[k]
            if halted or latched[s] or olat[s]:
                continue
            if no >= 77 or cnt[s] >= 30 or symcnt[s, sym[k]] >= 3:
                continue
            rc = 0
            for t in range(max(m - 9, 0), m + 1):
                rc += entm[s, t]
            if rc >= 30:
                continue
            entm[s, m] += 1; opn[no] = k; no += 1; cnt[s] += 1; symcnt[s, sym[k]] += 1
        q = 0
        for i in range(no):
            k = opn[i]
            if xm[k] <= m:
                realized[si[k]] += rr[k]; cnt[si[k]] -= 1; symcnt[si[k], sym[k]] -= 1
            else:
                opn[q] = k; q += 1
        no = q
        ps = realized.copy()
        es = np.zeros(N)
        for i in range(no):
            k = opn[i]
            j = min(m - em[k], n[k] - 1)
            if j < 0:
                j = 0
            c = path[off[k] + j]
            ps[si[k]] += side[k] * (c - ent[k]) / risk[k] - lc[k]
            es[si[k]] += bb[k]
        if lo:
            for s in range(N):
                if ps[s] <= -2.0 + 1e-12:
                    olat[s] = True
        tot = ps.sum()
        if tot <= -20.0 + 1e-12:
            halted = True
        ix = m - 570
        if 0 <= ix < 390:
            TB[ix] = tot
            EE[ix] = es.sum()
            for s in range(N):
                ES[s, ix] = es[s]
    for i in range(no):
        k = opn[i]
        realized[si[k]] += rr[k]
    fin = realized.sum()
    for ix in range(max(mlast - 570 + 1, 0), 390):
        TB[ix] = fin
    for s in range(N):
        outR[s] = realized[s]


@njit(parallel=True, cache=True)
def run_days(st, si, sym, side, ent, risk, lc, em, xm, rr, off, n, bb, lo, path):
    D = len(st) - 1
    R = np.zeros((D, N)); TB = np.zeros((D, 390)); EE = np.zeros((D, 390)); ES = np.zeros((D, N, 390))
    for d in prange(D):
        sim_day(st[d], st[d + 1], si, sym, side, ent, risk, lc, em, xm, rr, off, n, bb, lo, path, R[d], TB[d], EE[d], ES[d])
    return R, TB, EE, ES
