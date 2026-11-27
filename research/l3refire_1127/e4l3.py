"""L3REFIRE-1127: E4 minute book engine = research/cfprimary_1127/e4nb.py sim_day copied line by line, plus ONE added
entry check for setup 0 (L3-gap-slope-fromopen-FD) only, per symbol per session (PREREG.md):
  mode 0 off (must equal e4nb exactly) | 1 max `par` open L3 lots per name | 2 no L3 entry within `par` minutes of the
  prior taken L3 entry in that name (par huge = one entry per name per day) | 3 no L3 entry in a name after an L3 lot
  in that name exited at its stop (bench10 kind == 1) earlier that day.
Rules otherwise unchanged: 77 slots, 30 lots per setup, <= 3 per symbol per setup, burst brake 30 / 10 min, -2R realised
latch, LATCH-OPEN when lo, -20R closed+open halt. Locked block asserted absent at load.
Educational only - not financial advice."""
import sys
import numpy as np
from numba import njit, prange

sys.path.insert(0, "research/cfprimary_1127")
import e4nb as E  # noqa: E402

N = E.N
SETUPS = E.SETUPS


def load(W):
    import pandas as pd
    C, days, st, PATH, A = E.load(W)
    A["kind"] = C.kind.to_numpy(np.int64)
    E.no_locked(days)
    return C, days, st, PATH, A


@njit(cache=True)
def sim_day(a, b, si, sym, side, ent, risk, lc, em, xm, rr, off, n, kind, keep, f, lo, mode, par, path, outR, outN, taken):
    realized = np.zeros(N); nl = np.zeros(N, np.int64)
    latched = np.zeros(N, np.bool_); olat = np.zeros(N, np.bool_)
    cnt = np.zeros(N, np.int64)
    nsym = 0
    for k in range(a, b):
        if sym[k] + 1 > nsym:
            nsym = sym[k] + 1
    symcnt = np.zeros((N, nsym + 1), np.int64)
    lastent = np.full(nsym + 1, -10 ** 7, np.int64)   # added: last taken L3 entry minute per symbol
    stopped = np.zeros(nsym + 1, np.bool_)             # added: an L3 lot in the symbol exited at its stop
    entm = np.zeros((N, 1000), np.int64)
    opn = np.empty(b - a, np.int64); no = 0
    m0 = 10 ** 9; last = -1
    for k in range(a, b):
        if keep[k]:
            if em[k] < m0:
                m0 = em[k]
            if em[k] > last:
                last = em[k]
    if last < 0:
        for s in range(N):
            outR[s] = 0.0; outN[s] = 0
        return
    halted = False
    p = a
    for m in range(m0, 956):
        if m > last and no == 0:
            break
        q = 0
        for i in range(no):
            k = opn[i]
            if xm[k] <= m:
                realized[si[k]] += rr[k] * f; cnt[si[k]] -= 1; symcnt[si[k], sym[k]] -= 1
                if si[k] == 0 and kind[k] == 1:
                    stopped[sym[k]] = True
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
            if not keep[k]:
                continue
            s = si[k]
            if halted or latched[s] or olat[s]:
                continue
            if no >= 77 or cnt[s] >= 30 or symcnt[s, sym[k]] >= 3:
                continue
            if s == 0 and mode > 0:                     # added L3-only check
                if mode == 1 and symcnt[0, sym[k]] >= par:
                    continue
                if mode == 2 and m - lastent[sym[k]] < par:
                    continue
                if mode == 3 and stopped[sym[k]]:
                    continue
            rc = 0
            for t in range(max(m - 9, 0), m + 1):
                rc += entm[s, t]
            if rc >= 30:
                continue
            entm[s, m] += 1; nl[s] += 1; taken[k] = True; opn[no] = k; no += 1; cnt[s] += 1; symcnt[s, sym[k]] += 1
            if s == 0:
                lastent[sym[k]] = m
        q = 0
        for i in range(no):
            k = opn[i]
            if xm[k] <= m:
                realized[si[k]] += rr[k] * f; cnt[si[k]] -= 1; symcnt[si[k], sym[k]] -= 1
                if si[k] == 0 and kind[k] == 1:
                    stopped[sym[k]] = True
            else:
                opn[q] = k; q += 1
        no = q
        ps = realized.copy()
        for i in range(no):
            k = opn[i]
            j = min(m - em[k], n[k] - 1)
            if j < 0:
                j = 0
            c = path[off[k] + j]
            ps[si[k]] += (side[k] * (c - ent[k]) / risk[k] - lc[k]) * f
        if lo:
            for s in range(N):
                if ps[s] <= -2.0 + 1e-12:
                    olat[s] = True
        tot = ps.sum()
        if tot <= -20.0 + 1e-12:
            halted = True
    for i in range(no):
        k = opn[i]
        realized[si[k]] += rr[k] * f
    for s in range(N):
        outR[s] = realized[s]; outN[s] = nl[s]


@njit(parallel=True, cache=True)
def run_days(dix, st, si, sym, side, ent, risk, lc, em, xm, rr, off, n, kind, keep, fday, lo, mode, par, path):
    D = len(dix)
    R = np.zeros((D, N)); NL = np.zeros((D, N), np.int64); TK = np.zeros(len(si), np.bool_)
    for q in prange(D):
        d = dix[q]
        sim_day(st[d], st[d + 1], si, sym, side, ent, risk, lc, em, xm, rr, off, n, kind, keep, fday[q], lo, mode, par,
                path, R[q], NL[q], TK)
    return R, NL, TK


def run(A, st, PATH, dix, keep, lo, mode=0, par=0, fday=None):
    dix = np.asarray(dix, np.int64)
    fd = np.ones(len(dix)) if fday is None else np.asarray(fday, np.float64)
    return run_days(dix, st, A["si"], A["sym"], A["side"], A["ent"], A["risk"], A["lc"], A["em"], A["xm"], A["rr"],
                    A["off"], A["n"], A["kind"], np.asarray(keep, np.bool_), fd, lo, int(mode), int(par), PATH)
