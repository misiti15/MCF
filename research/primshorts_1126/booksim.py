"""PRIMSHORTS-1126 minute book engine for the Friday lineup options (after research/squeeze_1125/sim.py, the neveragain
engine): Primary book rules - <= 77 open lots, <= 30 per setup, <= 3 per setup per symbol, burst brake 30 entries / 10 min
per setup, -2R per-setup latch (realised; LATCH-OPEN = realised + open marks), -20R account halt on realised + open
marks (LR3). Options: per-setup weight w (book R = w x lot R; the latch counts the setup's own lot R) and per-setup LO flag.
Educational only - not financial advice."""
import numpy as np


def sim_day(si, sym, side, ent, risk, lc, em, xm, rr, markf, N, w, lo_set, cap=77, scap=30, symcap=3, H=20.0):
    """si setup idx, markf(idx_array, m) -> open R marks (after costs; nan = no mark) of those lots at minute m.
    Returns per-setup realised R (unweighted lot R summed), lots taken mask, weighted day R, trough."""
    by_m = {}
    for k in range(len(si)):
        by_m.setdefault(int(em[k]), []).append(k)
    if not by_m:
        return np.zeros(N), np.zeros(len(si), bool), 0.0, 0.0
    realized = np.zeros(N); latched = np.zeros(N, bool); olat = np.zeros(N, bool)
    taken = np.zeros(len(si), bool); open_ = []; cnt = np.zeros(N, int); symcnt = {}; recent = [[] for _ in range(N)]
    halted = False; trough = 0.0
    m0, last = min(by_m), max(by_m)

    def realize(m):
        nonlocal open_
        keep = []
        for k in open_:
            if xm[k] <= m:
                realized[si[k]] += rr[k]; cnt[si[k]] -= 1; symcnt[(si[k], sym[k])] -= 1
            else:
                keep.append(k)
        open_ = keep
    for m in range(m0, 960):
        if m > last and not open_:
            break
        realize(m)
        latched[realized <= -2.0 + 1e-12] = True
        for k in by_m.get(m, ()):
            s = si[k]
            if halted or latched[s] or olat[s]:
                continue
            if len(open_) >= cap or cnt[s] >= scap or symcnt.get((s, sym[k]), 0) >= symcap:
                continue
            recent[s] = [t for t in recent[s] if t > m - 10]
            if len(recent[s]) >= 30:
                continue
            recent[s].append(m); open_.append(k); cnt[s] += 1; taken[k] = True
            symcnt[(s, sym[k])] = symcnt.get((s, sym[k]), 0) + 1
        realize(m)
        ps = realized.copy()
        if open_:
            o = np.asarray(open_)
            v = np.nan_to_num(markf(o, m))
            ps += np.bincount(si[o], weights=v, minlength=N)
        olat |= lo_set & (ps <= -2.0 + 1e-12)
        tot = float((ps * w).sum()); trough = min(trough, tot)
        if tot <= -H + 1e-12:
            halted = True
    for k in open_:
        realized[si[k]] += rr[k]
    return realized, taken, float((realized * w).sum()), trough
