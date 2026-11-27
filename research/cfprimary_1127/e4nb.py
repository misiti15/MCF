"""CF-PRIMARY: E4 minute book engine (squeeze_1125 / hedgeb_1126 sim_day, Primary rules) ported line by line to numba,
with a per-lot keep mask (CF / random removal) and a constant size factor (constant-cut control). RAW book only.
Rules: 77 slots, 30 lots per setup, <= 3 per symbol per setup, burst brake 30 entries / 10 min per setup, -2R realised
latch, LATCH-OPEN (closed + open <= -2R) when lo, -20R closed+open halt. Locked block asserted absent at load.
Educational only - not financial advice."""
from pathlib import Path
import numpy as np
import pandas as pd
from numba import njit, prange

SETUPS = ["L3-gap-slope-fromopen-FD", "RW3-gapdn-rsi5pop-flowsell-short-FD",
          "RW5-heat30-flowsell-rsi5pop-gapdn-short-FD", "NM-ETF-late-dip-di-long"]
N = 4
LOCK = ("2024-11-01", "2025-02-28")


def no_locked(dates):
    d = pd.Series(list(dates)).astype(str)
    assert not ((d >= LOCK[0]) & (d <= LOCK[1])).any(), "locked block row found"


def load(W):
    W = Path(W)
    C = pd.read_parquet(W / "cand.parquet")
    C["date"] = C.date.astype(str)
    no_locked(C.date.unique())
    C["si"] = C.setup.map({s: i for i, s in enumerate(SETUPS)})
    C = C.sort_values(["date", "em", "si", "symbol"], kind="mergesort").reset_index(drop=True)
    C["sym"] = C.groupby("date").symbol.transform(lambda s: pd.factorize(s)[0])
    days = C.date.drop_duplicates().tolist()
    st = np.r_[np.flatnonzero(C.date.ne(C.date.shift()).to_numpy()), len(C)]
    PATH = np.load(W / "paths.npy").astype(np.float64)
    A = dict(si=C.si.to_numpy(np.int64), sym=C.sym.to_numpy(np.int64), side=C.side.to_numpy(np.float64),
             ent=C.entry.to_numpy(np.float64), risk=C.risk.to_numpy(np.float64), lc=C.lcost.to_numpy(np.float64),
             em=C.em.to_numpy(np.int64), xm=C.xm.to_numpy(np.int64), rr=C.r.to_numpy(np.float64),
             off=C.off.to_numpy(np.int64), n=C.n.to_numpy(np.int64))
    return C, days, st.astype(np.int64), PATH, A


@njit(cache=True)
def sim_day(a, b, si, sym, side, ent, risk, lc, em, xm, rr, off, n, keep, f, lo, path, outR, outN, taken):
    realized = np.zeros(N); nl = np.zeros(N, np.int64)
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
        # realize
        q = 0
        for i in range(no):
            k = opn[i]
            if xm[k] <= m:
                realized[si[k]] += rr[k] * f; cnt[si[k]] -= 1; symcnt[si[k], sym[k]] -= 1
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
            rc = 0
            for t in range(max(m - 9, 0), m + 1):
                rc += entm[s, t]
            if rc >= 30:
                continue
            entm[s, m] += 1; nl[s] += 1; taken[k] = True; opn[no] = k; no += 1; cnt[s] += 1; symcnt[s, sym[k]] += 1
        q = 0
        for i in range(no):
            k = opn[i]
            if xm[k] <= m:
                realized[si[k]] += rr[k] * f; cnt[si[k]] -= 1; symcnt[si[k], sym[k]] -= 1
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
def run_days(dix, st, si, sym, side, ent, risk, lc, em, xm, rr, off, n, keep, fday, lo, path):
    D = len(dix)
    R = np.zeros((D, N)); NL = np.zeros((D, N), np.int64); TK = np.zeros(len(si), np.bool_)
    for q in prange(D):
        d = dix[q]
        sim_day(st[d], st[d + 1], si, sym, side, ent, risk, lc, em, xm, rr, off, n, keep, fday[q], lo, path, R[q], NL[q], TK)
    return R, NL, TK


def run(A, st, PATH, dix, keep, lo, fday=None):
    dix = np.asarray(dix, np.int64)
    fd = np.ones(len(dix)) if fday is None else np.asarray(fday, np.float64)
    return run_days(dix, st, A["si"], A["sym"], A["side"], A["ent"], A["risk"], A["lc"], A["em"], A["xm"], A["rr"],
                    A["off"], A["n"], np.asarray(keep, np.bool_), fd, lo, PATH)
