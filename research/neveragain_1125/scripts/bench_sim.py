"""NEVERAGAIN bench: minute-by-minute P4 book with guards G1-G5 (PLAN.md). Educational only - not financial advice.
Usage: python bench_sim.py WORK BOOK(RAW|NEUTRAL|P10|E<x>) CFG[,CFG...]   (CFG: NOW G1-2 G1-3 G2-6 G3 G3-L G4,
combos 'G1-3+G4', placebo 'PLC<k>' = G3 with day-permuted index paths, draw k)"""
import sys
from multiprocessing import Pool
from pathlib import Path
import numpy as np
import pandas as pd

W = Path(sys.argv[1]); BOOK = sys.argv[2]; CFGS = sys.argv[3].split(",")
SETUPS = ["L3-gap-slope-fromopen-FD", "RW3-gapdn-rsi5pop-flowsell-short-FD", "RW5-heat30-flowsell-rsi5pop-gapdn-short-FD",
          "NM-ETF-late-dip-di-long"]
N = len(SETUPS); GD = np.array([1, 1, 1, 0], bool)
BASE = {"NOW": (None, None, None, False), "G1-2": (2.0, None, None, False), "G1-3": (3.0, None, None, False),
        "G2-6": (None, 6, None, False), "G3": (None, None, 0.5, False), "G3-L": (None, None, 0.3, False),
        "G4": (None, None, None, True)}


def parse(name):
    if name.startswith("PLC"):
        return (None, None, 0.5, False)
    lo = lc = it = None; k4 = False
    for p in name.split("+"):
        a, b, c, d = BASE[p]
        lo, lc, it, k4 = a or lo, b or lc, c or it, k4 or d
    return lo, lc, it, k4


C = pd.read_parquet(W / "cand.parquet")
C = C[C.setup.isin(SETUPS)].copy()
PATH = np.load(W / "paths.npy", mmap_mode="r")
IDX = np.load(W / "idx.npy"); IDAYS = pd.read_csv(W / "idx_days.csv").iloc[:, 0].astype(str).tolist()
IPOS = {d: i for i, d in enumerate(IDAYS)}
C["si"] = C.setup.map({s: i for i, s in enumerate(SETUPS)})
C = C.sort_values(["date", "em", "si", "symbol"], kind="mergesort").reset_index(drop=True)
SHIFT = np.zeros(N)
if BOOK != "RAW":
    a = pd.read_csv(W / "avg_P4.csv").set_index("setup").a.reindex(SETUPS).fillna(0).to_numpy()
    if BOOK == "NEUTRAL":
        SHIFT = a
    elif BOOK == "P10":
        SHIFT = a - 0.10
    elif BOOK.startswith("E"):          # zero-expectancy + edge e per lot
        SHIFT = a - float(BOOK[1:])
DAYS = []
for d, g in C.groupby("date"):
    DAYS.append((d, dict(si=g.si.to_numpy(), sym=pd.factorize(g.symbol)[0], side=g.side.to_numpy(float),
                         ent=g.entry.to_numpy(float), risk=g.risk.to_numpy(float), lc=g.lcost.to_numpy(float),
                         em=g.em.to_numpy(int), xm=g.xm.to_numpy(int), rr=g.r.to_numpy(float),
                         off=g.off.to_numpy(int), n=g.n.to_numpy(int))))


def idx_ok_fn(ix, thr):
    """block[m] for m in 570..959: SPY & IWM >= thr% above open at close m-1 and above close m-31."""
    blk = np.zeros(960, bool)
    if ix is None:
        return blk
    a = IDX[ix]
    for m in range(601, 960):
        j = min(m - 570, 390)
        s, w = a[0], a[1]
        if s[j] / s[0] - 1 >= thr / 100 and w[j] / w[0] - 1 >= thr / 100 and s[j] > s[j - 30] and w[j] > w[j - 30]:
            blk[m] = True
    return blk


def sim_day(G, Lo, cap, blk, X, H=20.0):
    si, sym, side, ent, risk, lc = G["si"], G["sym"], G["side"], G["ent"], G["risk"], G["lc"]
    em, xm, off, n = G["em"], G["xm"], G["off"], G["n"]
    sh = SHIFT[si]; rr = G["rr"] - sh
    dur = np.maximum(xm - em, 1).astype(float)
    by_m = {}
    for k in range(len(si)):
        by_m.setdefault(em[k], []).append(k)
    realized = np.zeros(N); nl = np.zeros(N, int); latched = np.zeros(N, bool); olat = np.zeros(N, bool)
    open_ = []; cnt = np.zeros(N, int); symcnt = {}
    halted = stopped = False; stop_m = -1; g1f = np.zeros(N, bool); g2n = 0; g3n = 0
    recent = [[] for _ in range(N)]
    trough = 0.0
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
    for m in range(m0, 956):
        if m > last and not open_:
            break
        realize(m)
        latched[realized <= -2.0 + 1e-12] = True
        for k in by_m.get(m, ()):
            s = si[k]
            if halted or stopped or latched[s]:
                continue
            if olat[s]:
                g1f[s] = True; continue
            if len(open_) >= 77 or cnt[s] >= 30 or symcnt.get((s, sym[k]), 0) >= 3:
                continue
            if cap is not None and cnt[s] >= cap:
                g2n += 1; continue
            if blk is not None and GD[s] and blk[m]:
                g3n += 1; continue
            recent[s] = [t for t in recent[s] if t > m - 10]
            if len(recent[s]) >= 30:
                continue
            recent[s].append(m); nl[s] += 1; open_.append(k); cnt[s] += 1
            symcnt[(s, sym[k])] = symcnt.get((s, sym[k]), 0) + 1
        realize(m)
        if open_:
            o = np.array(open_)
            j = np.minimum(m - em[o], n[o] - 1)
            c = PATH[off[o] + np.maximum(j, 0)]
            mk = side[o] * (c - ent[o]) / risk[o] - lc[o] - sh[o] * np.clip((m - em[o]) / dur[o], 0, 1)
            ps = realized + np.bincount(si[o], weights=mk, minlength=N)
        else:
            o = np.zeros(0, int); mk = np.zeros(0); ps = realized.copy()
        if Lo is not None:
            olat |= ps <= -Lo + 1e-12
        tot = ps.sum(); trough = min(trough, tot)
        if tot <= -H + 1e-12:
            halted = True
        if X is not None and tot <= -X + 1e-12:
            stopped = True; stop_m = m
            for k, v in zip(o, mk):
                realized[si[k]] += v
            open_ = []
            break
    for k in open_:
        realized[si[k]] += rr[k]
    return realized, nl, stop_m, trough, g1f.sum(), g2n, g3n


def run(cfgname):
    Lo, cap, thr, k4 = parse(cfgname)
    perm = None
    if cfgname.startswith("PLC"):
        rng = np.random.default_rng(1125 + int(cfgname[3:]))
        perm = rng.permutation(len(IDAYS))
    D = [d for d, _ in DAYS]
    iso = pd.to_datetime(pd.Series(D)).dt.isocalendar()
    wk = (iso.year.astype(str) + "-" + iso.week.astype(str).str.zfill(2)).to_numpy()
    first = {}
    for i, w in enumerate(wk):
        first.setdefault(w, i)
    fin = np.zeros((len(D), N)); rows = []; cal = {}
    for i, (d, G) in enumerate(DAYS):
        j = first[wk[i]]
        if j not in cal:
            if j >= 120:
                tot = fin[max(0, j - 250):j].sum(1)
                cal[j] = (float(np.clip(4 * tot.std(ddof=1), 2.5 * N, 8 * N)), True)
            else:
                cal[j] = (None, False)
        X, scored = cal[j]
        blk = None
        if thr is not None:
            ix = IPOS.get(d)
            if perm is not None and ix is not None:
                ix = int(perm[ix])
            blk = idx_ok_fn(ix, thr)
        r, nl, sm, tr, g1, g2, g3 = sim_day(G, Lo, cap, blk, X if k4 else None)
        fin[i] = r
        row = dict(date=d, scored=scored, X=X if k4 and X else np.nan, stop_m=sm, trough=tr, g1=g1, g2=g2, g3=g3)
        for s in range(N):
            row[f"R{s}"] = r[s]; row[f"N{s}"] = nl[s]
        rows.append(row)
    out = pd.DataFrame(rows)
    out.to_parquet(W / f"day_{BOOK}_{cfgname}.parquet", index=False)
    sc = out[out.scored]
    return cfgname, round(sum(sc[f"R{s}"].sum() for s in range(N)), 1)


if __name__ == "__main__":
    with Pool(min(3, len(CFGS))) as p:
        for c, tot in p.imap_unordered(run, CFGS):
            print(BOOK, c, tot, flush=True)
