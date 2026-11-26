"""SQUEEZE_1125 bench: neveragain bench_sim engine (P4 Primary book) + LATCH-OPEN, R1 NET-BETA BUDGET, R2 SQUEEZE EXIT.
Usage: python sim.py W BOOK(RAW|NEUTRAL) CFG[,CFG...]  CFG = BASE | LO | B8 | B12 | B16 | SV | SO | LO+B8 ... (PREREG.md)
Educational only - not financial advice."""
import sys
from multiprocessing import Pool
from pathlib import Path
import numpy as np
import pandas as pd

W = Path(sys.argv[1]); BOOK = sys.argv[2]; CFGS = sys.argv[3].split(",")
SETUPS = ["L3-gap-slope-fromopen-FD", "RW3-gapdn-rsi5pop-flowsell-short-FD",
          "RW5-heat30-flowsell-rsi5pop-gapdn-short-FD", "NM-ETF-late-dip-di-long"]
N = len(SETUPS)
LOCK = ("2024-11-01", "2025-02-28")


def parse(name):
    lo = False; bud = None; sq = None
    for p in name.split("+"):
        if p == "LO":
            lo = True
        elif p.startswith("B") and p != "BASE":
            bud = float(p[1:])
        elif p == "SV":
            sq = "vwap"
        elif p == "SO":
            sq = "open"
    return lo, bud, sq


C = pd.read_parquet(W / "cand.parquet")
d_ = C.date.astype(str)
assert not ((d_ >= LOCK[0]) & (d_ <= LOCK[1])).any()
PATH = np.load(W / "paths.npy", mmap_mode="r")
SPY = np.load(W / "spy.npy"); SDAYS = pd.read_csv(W / "spy_days.csv").iloc[:, 0].astype(str).tolist()
SPOS = {d: i for i, d in enumerate(SDAYS)}
C["si"] = C.setup.map({s: i for i, s in enumerate(SETUPS)})
C = C.sort_values(["date", "em", "si", "symbol"], kind="mergesort").reset_index(drop=True)
SHIFT = np.zeros(N)
if BOOK == "NEUTRAL":
    SHIFT = pd.read_csv(W / "avg_base.csv").set_index("setup").a.reindex(SETUPS).fillna(0).to_numpy()
C["b"] = C.side * C.beta * 0.01 * C.entry / C.risk
DAYS = []
for d, g in C.groupby("date"):
    DAYS.append((d, g.per.iloc[0], dict(si=g.si.to_numpy(), sym=pd.factorize(g.symbol)[0], side=g.side.to_numpy(float),
                                        ent=g.entry.to_numpy(float), risk=g.risk.to_numpy(float), lc=g.lcost.to_numpy(float),
                                        em=g.em.to_numpy(int), xm=g.xm.to_numpy(int), rr=g.r.to_numpy(float),
                                        off=g.off.to_numpy(int), n=g.n.to_numpy(int), b=g.b.to_numpy(float))))


def squeeze_triggers(d, mode):
    """(short_k, long_k): bar index k (minute 570+k) whose close triggers; -1 if none. PREREG R2."""
    i = SPOS.get(d)
    if i is None:
        return -1, -1
    a = SPY[i]; o = a[0]; c = a[1:391]; vw = a[391:781]
    lvl = vw if mode == "vwap" else np.full(390, o)
    sk = lk = -1
    lowseen = hiseen = False
    for k in range(390):
        if k >= 1:
            lowseen = lowseen or c[k - 1] <= o * (1 - 0.004)
            hiseen = hiseen or c[k - 1] >= o * (1 + 0.004)
        if k < 30 or k > 380:
            continue
        r30 = c[k] / c[k - 30] - 1
        if sk < 0 and lowseen and c[k] >= lvl[k] and r30 > 0.005:
            sk = k
        if lk < 0 and hiseen and c[k] <= lvl[k] and r30 < -0.005:
            lk = k
    return sk, lk


def sim_day(G, lo, bud, sqk, H=20.0):
    si, sym, side, ent, risk, lc = G["si"], G["sym"], G["side"], G["ent"], G["risk"], G["lc"]
    em, xm, off, n, bb = G["em"], G["xm"], G["off"], G["n"], G["b"]
    sh = SHIFT[si]; rr = G["rr"] - sh
    dur = np.maximum(xm - em, 1).astype(float)
    by_m = {}
    for k in range(len(si)):
        by_m.setdefault(em[k], []).append(k)
    realized = np.zeros(N); nl = np.zeros(N, int); latched = np.zeros(N, bool); olat = np.zeros(N, bool)
    open_ = []; cnt = np.zeros(N, int); symcnt = {}
    halted = False; recent = [[] for _ in range(N)]
    trough = 0.0; nb = 0.0
    r1blk = 0; r2blk = 0; r2closed = 0; r2act = False
    s_k, l_k = sqk if sqk is not None else (-1, -1)
    s_m = 570 + s_k + 1 if s_k >= 0 else 10 ** 6     # action minute (close of bar k+1); block from this minute on
    l_m = 570 + l_k + 1 if l_k >= 0 else 10 ** 6
    m0, last = min(by_m), max(by_m)

    def realize(m):
        nonlocal open_, nb
        keep = []
        for k in open_:
            if xm[k] <= m:
                realized[si[k]] += rr[k]; cnt[si[k]] -= 1; symcnt[(si[k], sym[k])] -= 1; nb -= bb[k]
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
            if halted or latched[s] or olat[s]:
                continue
            if len(open_) >= 77 or cnt[s] >= 30 or symcnt.get((s, sym[k]), 0) >= 3:
                continue
            if (side[k] < 0 and m >= s_m) or (side[k] > 0 and m >= l_m):
                r2blk += 1; r2act = True; continue
            if bud is not None and ((side[k] < 0 and nb <= -bud) or (side[k] > 0 and nb >= bud)):
                r1blk += 1; continue
            recent[s] = [t for t in recent[s] if t > m - 10]
            if len(recent[s]) >= 30:
                continue
            recent[s].append(m); nl[s] += 1; open_.append(k); cnt[s] += 1; nb += bb[k]
            symcnt[(s, sym[k])] = symcnt.get((s, sym[k]), 0) + 1
        realize(m)
        if open_:
            o = np.array(open_)
            j = np.minimum(m - em[o], n[o] - 1)
            c = PATH[off[o] + np.maximum(j, 0)]
            mk = side[o] * (c - ent[o]) / risk[o] - lc[o] - sh[o] * np.clip((m - em[o]) / dur[o], 0, 1)
            # R2 action: flatten the side at this minute's close
            if m == s_m or m == l_m:
                fl = (side[o] < 0) if m == s_m else (side[o] > 0)
                if m == s_m and m == l_m:
                    fl = np.ones(len(o), bool)
                keep = []
                for q, k in enumerate(o):
                    if fl[q]:
                        realized[si[k]] += mk[q]; cnt[si[k]] -= 1; symcnt[(si[k], sym[k])] -= 1; nb -= bb[k]
                        r2closed += 1; r2act = True
                    else:
                        keep.append(k)
                open_ = keep
                o = o[~fl]; mk = mk[~fl]
            ps = realized + np.bincount(si[o], weights=mk, minlength=N) if len(o) else realized.copy()
        else:
            ps = realized.copy()
        if lo:
            olat |= ps <= -2.0 + 1e-12
        tot = ps.sum(); trough = min(trough, tot)
        if tot <= -H + 1e-12:
            halted = True
    for k in open_:
        realized[si[k]] += rr[k]
    return realized, nl, trough, r1blk, r2blk, r2closed, r2act


def run(cfgname):
    lo, bud, sq = parse(cfgname)
    rows = []
    for d, per, G in DAYS:
        sqk = squeeze_triggers(d, sq) if sq else None
        r, nl, tr, b1, b2, c2, act = sim_day(G, lo, bud, sqk)
        row = dict(date=d, per=per, trough=tr, r1blk=b1, r2blk=b2, r2closed=c2, r2act=act,
                   s_k=sqk[0] if sqk else -1, l_k=sqk[1] if sqk else -1)
        for s in range(N):
            row[f"R{s}"] = r[s]; row[f"N{s}"] = nl[s]
        rows.append(row)
    out = pd.DataFrame(rows)
    out.to_parquet(W / f"day_{BOOK}_{cfgname}.parquet", index=False)
    return cfgname, round(sum(out[f"R{s}"].sum() for s in range(N)), 1)


if __name__ == "__main__":
    with Pool(min(3, len(CFGS))) as p:
        for c, tot in p.imap_unordered(run, CFGS):
            print(BOOK, c, tot, flush=True)
