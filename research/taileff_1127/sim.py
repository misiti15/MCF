"""TAILEFF-1127 book runs on the squeeze_1125 / neveragain minute engine (E4; research/squeeze_1125/sim.py sim_day logic
re-used) plus G1-3, SCALED-K4, SHOCK-V, the per-setup -8R cap (S8), exposure (risk-minutes) and size-matched random blocks.
Usage: python sim.py W BOOK(RAW|Z|P) CFG[,CFG...]
CFG = BASE | LO | G1-3 | LO+B8 | LO+K4+SHK | LO+S8 | LO+B8+K4 | RB<ref>~<cfg>~<seed> (random block, PREREG.md).
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
PERS = ["FIT", "CHECK", "T2"]


def parse(name):
    c = dict(lo=None, bud=None, k4=False, shk=False, s8=False)
    for p in name.split("+"):
        if p == "LO":
            c["lo"] = 2.0
        elif p == "G1-3":
            c["lo"] = 3.0
        elif p.startswith("B") and p != "BASE":
            c["bud"] = float(p[1:])
        elif p == "K4":
            c["k4"] = True
        elif p == "SHK":
            c["shk"] = True
        elif p == "S8":
            c["s8"] = True
    return c


C = pd.read_parquet(W / "cand.parquet")
d_ = C.date.astype(str)
assert not ((d_ >= LOCK[0]) & (d_ <= LOCK[1])).any(), "locked block row found"
PATH = np.load(W / "paths.npy", mmap_mode="r")
C["si"] = C.setup.map({s: i for i, s in enumerate(SETUPS)})
C = C.sort_values(["date", "em", "si", "symbol"], kind="mergesort").reset_index(drop=True)
C["pk"] = C.per.map({p: i for i, p in enumerate(PERS)})
SH = np.zeros(len(C))
if BOOK in ("Z", "P"):
    a = pd.read_csv(W / "avg_base.csv")          # setup, per, a  (BASE RAW avg R per lot)
    amap = {(r.setup, r.per): r.a for r in a.itertuples()}
    SH = np.array([amap.get((s, p), 0.0) for s, p in zip(C.setup, C.per)]) - (0.10 if BOOK == "P" else 0.0)
C["sh"] = SH
C["b"] = C.side * C.beta * 0.01 * C.entry / C.risk
DAYS = []
for d, g in C.groupby("date"):
    DAYS.append((d, g.per.iloc[0], g.index.to_numpy(),
                 dict(si=g.si.to_numpy(), sym=pd.factorize(g.symbol)[0], side=g.side.to_numpy(float),
                      ent=g.entry.to_numpy(float), risk=g.risk.to_numpy(float), lc=g.lcost.to_numpy(float),
                      em=g.em.to_numpy(int), xm=g.xm.to_numpy(int), rr=g.r.to_numpy(float), sh=g.sh.to_numpy(float),
                      off=g.off.to_numpy(int), n=g.n.to_numpy(int), b=g.b.to_numpy(float), pk=g.pk.to_numpy(int))))
DAYS.sort(key=lambda t: t[0])


def sim_day(G, cf, X, blk=None, H=20.0):
    si, sym, side, ent, risk, lc = G["si"], G["sym"], G["side"], G["ent"], G["risk"], G["lc"]
    em, xm, off, n, bb, sh = G["em"], G["xm"], G["off"], G["n"], G["b"], G["sh"]
    rr = G["rr"] - sh
    dur = np.maximum(xm - em, 1).astype(float)
    by_m = {}
    for k in range(len(si)):
        by_m.setdefault(em[k], []).append(k)
    realized = np.zeros(N); nl = np.zeros(N, int); expo = np.zeros(N)
    latched = np.zeros(N, bool); olat = np.zeros(N, bool); s8blk = np.zeros(N, bool)
    open_ = []; cnt = np.zeros(N, int); symcnt = {}
    halted = False; k4hit = False; shkhit = False; recent = [[] for _ in range(N)]
    trough = 0.0; nb = 0.0; b8blk = 0; s8f = 0; vprev = False; hist = []
    m0, last = min(by_m), max(by_m)
    lo, bud = cf["lo"], cf["bud"]
    v1t, v2t = max(8.0, 0.5 * X), max(12.0, 0.75 * X)

    def close_lot(k, val, m):
        nonlocal nb
        realized[si[k]] += val; cnt[si[k]] -= 1; symcnt[(si[k], sym[k])] -= 1; nb -= bb[k]
        expo[si[k]] += max(min(m, 955) - em[k], 1)

    def realize(m):
        nonlocal open_
        keep = []
        for k in open_:
            if xm[k] <= m:
                close_lot(k, rr[k], xm[k])
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
            if halted or k4hit or shkhit or latched[s] or olat[s] or s8blk[s]:
                continue
            if len(open_) >= 77 or cnt[s] >= 30 or symcnt.get((s, sym[k]), 0) >= 3:
                continue
            if blk is not None and blk[k]:
                continue
            if bud is not None and ((side[k] < 0 and nb <= -bud) or (side[k] > 0 and nb >= bud)):
                b8blk += 1; continue
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
            ps = realized + np.bincount(si[o], weights=mk, minlength=N)
            if cf["s8"]:
                hit = ps <= -8.0 + 1e-12
                if hit.any():
                    keep = []
                    for q, k in enumerate(o):
                        if hit[si[k]]:
                            close_lot(k, mk[q], m)
                        else:
                            keep.append(k)
                    s8f += int((hit & ~s8blk).sum()); s8blk |= hit
                    open_ = keep; sel = ~hit[si[o]]; o, mk = o[sel], mk[sel]
                    ps = realized + (np.bincount(si[o], weights=mk, minlength=N) if len(o) else 0.0)
            if cf["k4"] and ps.sum() <= -X + 1e-12:
                for q, k in enumerate(o):
                    close_lot(k, mk[q], m)
                open_ = []; k4hit = True
                ps = realized.copy()
        else:
            ps = realized.copy()
        if lo is not None:
            olat |= ps <= -lo + 1e-12
        tot = ps.sum(); trough = min(trough, tot)
        if tot <= -H + 1e-12:
            halted = True
        if cf["shk"]:
            v = (len(hist) >= 1 and max(hist[-2:]) - tot >= v1t) or (len(hist) >= 1 and max(hist[-10:]) - tot >= v2t)
            if v and vprev:
                shkhit = True
            vprev = v
        hist.append(tot)
    for k in open_:
        close_lot(k, rr[k], xm[k])
    return realized, nl, expo, trough, b8blk, s8f, k4hit, shkhit


def run(cfgname):
    rb = cfgname.startswith("RB")
    if rb:                                   # RB<ref>~<cfg>~<seed>: ref rules with a size-matched random block
        ref, tgt, seed = cfgname[2:].split("~")
        cf = parse(ref)
        q = pd.read_csv(W / f"q_{BOOK if BOOK != 'P' else 'RAW'}_{ref}_{tgt}.csv")   # si, pk, q
        Q = np.zeros((N, len(PERS)))
        for r in q.itertuples():
            Q[r.si, r.pk] = r.q
        rng = np.random.default_rng(int(seed))
    else:
        cf = parse(cfgname)
    rows = []; finals = []; X = 32.0; wk = None
    for d, per, ix, G in DAYS:
        w = pd.Timestamp(d).isocalendar()[:2]
        if cf["k4"] and w != wk:
            wk = w
            tr = finals[-250:]
            X = float(np.clip(4 * np.std(tr, ddof=1), 10, 32)) if len(tr) >= 120 else 32.0
        blk = rng.random(len(G["si"])) < Q[G["si"], G["pk"]] if rb else None
        r, nl, ex, tr_, b8, s8, k4, shk = sim_day(G, cf, X, blk)
        finals.append(r.sum())
        row = dict(date=d, per=per, trough=tr_, b8blk=b8, s8f=s8, k4=k4, shk=shk, X=X)
        for s in range(N):
            row[f"R{s}"] = r[s]; row[f"N{s}"] = nl[s]; row[f"E{s}"] = ex[s]
        rows.append(row)
    out = pd.DataFrame(rows)
    assert not ((out.date >= LOCK[0]) & (out.date <= LOCK[1])).any()
    out.to_parquet(W / f"day_{BOOK}_{cfgname}.parquet", index=False)
    return cfgname, round(sum(out[f"R{s}"].sum() for s in range(N)), 1)


if __name__ == "__main__":
    with Pool(min(3, len(CFGS))) as p:
        for c, tot in p.imap_unordered(run, CFGS):
            print(BOOK, c, tot, flush=True)
