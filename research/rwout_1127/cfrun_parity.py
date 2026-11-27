"""RWOUT-1127 parity helper: research/cfprimary_1127/cfrun.py py_day copied verbatim (A, PATH passed in).
Educational only - not financial advice."""
import numpy as np


def py_day(A, PATH, a, b, keep, lo):
    """hedgeb_1126/hsim.py sim_day (RAW, no hedge state), verbatim logic, for the parity check."""
    si, sym, side, ent, risk, lc = A["si"][a:b], A["sym"][a:b], A["side"][a:b], A["ent"][a:b], A["risk"][a:b], A["lc"][a:b]
    em, xm, off, n, rr = A["em"][a:b], A["xm"][a:b], A["off"][a:b], A["n"][a:b], A["rr"][a:b]
    keep = keep[a:b]; N = 4
    by_m = {}
    for k in np.flatnonzero(keep):
        by_m.setdefault(em[k], []).append(k)
    realized = np.zeros(N); latched = np.zeros(N, bool); olat = np.zeros(N, bool)
    open_ = []; cnt = np.zeros(N, int); symcnt = {}; halted = False; recent = [[] for _ in range(N)]
    if not by_m:
        return realized
    m0, last = min(by_m), max(by_m)

    def realize(m):
        nonlocal open_
        kp = []
        for k in open_:
            if xm[k] <= m:
                realized[si[k]] += rr[k]; cnt[si[k]] -= 1; symcnt[(si[k], sym[k])] -= 1
            else:
                kp.append(k)
        open_ = kp
    for m in range(m0, 956):
        if m > last and not open_:
            break
        realize(m)
        latched[realized <= -2.0 + 1e-12] = True
        for k in by_m.get(m, ()):
            s = si[k]
            if halted or latched[s] or olat[s]:
                continue
            if len(open_) >= 77 or cnt[s] >= 30 or symcnt.get((s, sym[k]), 0) >= 3:
                continue
            recent[s] = [t for t in recent[s] if t > m - 10]
            if len(recent[s]) >= 30:
                continue
            recent[s].append(m); open_.append(k); cnt[s] += 1
            symcnt[(s, sym[k])] = symcnt.get((s, sym[k]), 0) + 1
        realize(m)
        if open_:
            o = np.array(open_)
            j = np.minimum(m - em[o], n[o] - 1)
            c = PATH[off[o] + np.maximum(j, 0)]
            mk = side[o] * (c - ent[o]) / risk[o] - lc[o]
            ps = realized + np.bincount(si[o], weights=mk, minlength=N)
        else:
            ps = realized.copy()
        if lo:
            olat |= ps <= -2.0 + 1e-12
        if ps.sum() <= -20.0 + 1e-12:
            halted = True
    for k in open_:
        realized[si[k]] += rr[k]
    return realized
