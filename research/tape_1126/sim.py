"""TAPE-1126 book runs on the squeeze_1125 / neveragain minute engine (E4; research/squeeze_1125/sim.py sim_day logic re-used,
plus per-lot block flags, per-lot weights and a per-day fade-family freeze minute). PREREG.md.
Usage: python sim.py CANDW SIGW OUT CONTEXT SETUPS(comma idx: P4|C) CFG[,CFG...]
CONTEXT = BASE | LO | L3OUT | LOL3OUT; CFG = base | S1 | S1c | S1r<seed> | S2 | S2c | S2r<seed> | S3 | S3p<seed>.
Educational only - not financial advice."""
import sys
from multiprocessing import Pool
from pathlib import Path
import numpy as np
import pandas as pd

CW, SW, OUT, CTX, BOOKN = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]), sys.argv[4], sys.argv[5]
CFGS = sys.argv[6].split(",")
LOCK = ("2024-11-01", "2025-02-28")
P4 = ["L3-gap-slope-fromopen-FD", "RW3-gapdn-rsi5pop-flowsell-short-FD",
      "RW5-heat30-flowsell-rsi5pop-gapdn-short-FD", "NM-ETF-late-dip-di-long"]
CONT = ["GEN-261020-09-EMAdChgge0p093-Z12lem0p82-VWAPcrossesle0-MID-QQQltm0p3-holdtr-long",
        "GEN-261023-07-RSIslopege9p1-BarRngATRge0p087-VWAPcrossesge8-LUNCH-BRvwgt0p7-hold-long"]
FADE = {0, 1, 2}
if BOOKN == "P4":
    SETUPS = P4; LONGS = {3}
else:                                   # one contender standalone: C0 / C1
    SETUPS = [CONT[int(BOOKN[1])]]; LONGS = {0}; FADE = set()
N = len(SETUPS)
LO = CTX in ("LO", "LOL3OUT"); L3OUT = CTX in ("L3OUT", "LOL3OUT")
OUT.mkdir(parents=True, exist_ok=True)

C = pd.read_parquet(CW / "cand.parquet")
C = C[C.setup.isin(SETUPS)].copy()
if L3OUT:
    C = C[C.setup != P4[0]]
d_ = C.date.astype(str)
assert not ((d_ >= LOCK[0]) & (d_ <= LOCK[1])).any(), "locked block row found"
PATH = np.load(CW / "paths.npy", mmap_mode="r")
SG = np.load(SW / "sig.npz")
SDAYS = SG["days"].astype(str); SPOS = {d: i for i, d in enumerate(SDAYS)}
assert not ((SDAYS >= LOCK[0]) & (SDAYS <= LOCK[1])).any()
FO5, TG, MKT, SEC = SG["fo5"], SG["TG"], SG["mkt"], SG["sec"]
C["si"] = C.setup.map({s: i for i, s in enumerate(SETUPS)})
C = C[C.date.isin(SPOS)].sort_values(["date", "em", "si", "symbol"], kind="mergesort").reset_index(drop=True)
C["b"] = C.side * C.beta * 0.01 * C.entry / C.risk
di = C.date.map(SPOS).to_numpy(); emk = np.clip(C.em.to_numpy() - 570, 0, 390)
fo = FO5[di, emk]
late = C.em.to_numpy() >= 690
ELIG = {"S1": C.si.isin(LONGS).to_numpy() & late & (C.side.to_numpy() > 0) & (C.beta.to_numpy() > 0),
        "S2": C.si.isin(FADE).to_numpy() & late}
FLAG = {"S1": ELIG["S1"] & (fo <= -0.003), "S2": ELIG["S2"] & (np.abs(fo) < 0.003)}
pkey = C.setup + "|" + C.per
PSH = {r: pd.Series(FLAG[r][ELIG[r]]).groupby(pkey[ELIG[r]].to_numpy()).mean() for r in ("S1", "S2")}
GROUPS = [(d, g.index.to_numpy()) for d, g in C.groupby("date")]
A = dict(si=C.si.to_numpy(), sym=pd.factorize(C.symbol)[0], side=C.side.to_numpy(float), ent=C.entry.to_numpy(float),
         risk=C.risk.to_numpy(float), lc=C.lcost.to_numpy(float), em=C.em.to_numpy(int), xm=C.xm.to_numpy(int),
         rr=C.r.to_numpy(float), off=C.off.to_numpy(int), n=C.n.to_numpy(int), b=C.b.to_numpy(float))
PER = C.groupby("date").per.first().to_dict()
TMIN = 570 + TG                          # decision minutes of the S3 grid (state at the end of minute T-1)


def sim_day(ix, blk, w, freeze_m, H=20.0):
    si, sym, side, ent, risk, lc = (A[k][ix] for k in ("si", "sym", "side", "ent", "risk", "lc"))
    em, xm, off, n, bb, rr = (A[k][ix] for k in ("em", "xm", "off", "n", "b", "rr"))
    blk = blk[ix]; w = w[ix]
    dur = np.maximum(xm - em, 1).astype(float)
    by_m = {}
    for k in range(len(si)):
        by_m.setdefault(em[k], []).append(k)
    realized = np.zeros(N); nl = np.zeros(N, int); latched = np.zeros(N, bool); olat = np.zeros(N, bool)
    open_ = []; cnt = np.zeros(N, int); symcnt = {}
    halted = False; recent = [[] for _ in range(N)]; nb = 0.0
    nbT = np.full(len(TMIN), np.nan); tq = {int(m) - 1: q for q, m in enumerate(TMIN)}
    m0, last = min(by_m), max(by_m)

    def realize(m):
        nonlocal open_, nb
        keep = []
        for k in open_:
            if xm[k] <= m:
                realized[si[k]] += w[k] * rr[k]; cnt[si[k]] -= 1; symcnt[(si[k], sym[k])] -= 1; nb -= bb[k]
            else:
                keep.append(k)
        open_ = keep
    for m in range(min(m0, 690), 956):
        if m > last and not open_ and m > int(TMIN[-1]):
            break
        realize(m)
        latched[realized <= -2.0 + 1e-12] = True
        for k in by_m.get(m, ()):
            s = si[k]
            if halted or latched[s] or olat[s] or blk[k]:
                continue
            if s in FADE and m >= freeze_m:
                continue
            if len(open_) >= 77 or cnt[s] >= 30 or symcnt.get((s, sym[k]), 0) >= 3:
                continue
            recent[s] = [t for t in recent[s] if t > m - 10]
            if len(recent[s]) >= 30:
                continue
            recent[s].append(m); nl[s] += 1; open_.append(k); cnt[s] += 1; nb += bb[k]
            symcnt[(s, sym[k])] = symcnt.get((s, sym[k]), 0) + 1
        realize(m)
        if m in tq:
            nbT[tq[m]] = nb
        if open_:
            o = np.array(open_)
            j = np.minimum(m - em[o], n[o] - 1)
            c = PATH[off[o] + np.maximum(j, 0)]
            mk = w[o] * (side[o] * (c - ent[o]) / risk[o] - lc[o])
            ps = realized + np.bincount(si[o], weights=mk, minlength=N)
        else:
            ps = realized.copy()
        if LO:
            olat |= ps <= -2.0 + 1e-12
        if ps.sum() <= -H + 1e-12:
            halted = True
    for k in open_:
        realized[si[k]] += w[k] * rr[k]
    return realized, nl, nbT


def masks(cfg):
    blk = np.zeros(len(C), bool); w = np.ones(len(C))
    for r in ("S1", "S2"):
        if cfg == r:
            blk = FLAG[r].copy()
        elif cfg.startswith(r + "r"):
            rng = np.random.default_rng(1126 * 1000 + int(cfg[3:]))
            p = pkey.map(PSH[r]).fillna(0).to_numpy()
            blk = ELIG[r] & (rng.random(len(C)) < p)
        elif cfg == r + "c":
            p = pkey.map(PSH[r]).fillna(0).to_numpy()
            w = np.where(ELIG[r], 1 - p, 1.0)
    return blk, w


def freeze_plan(cfg):
    """day -> (q, nb) fire index on the S3 grid, from this context's base run NB trajectory."""
    if not cfg.startswith("S3"):
        return {}
    base = pd.read_parquet(OUT / f"day_{CTX}_{BOOKN}_base.parquet")
    nbT = np.stack(base.nbT.to_numpy()); bd = base.date.tolist()
    plan = {}
    if cfg == "S3":
        for i, d in enumerate(bd):
            ok = MKT[SPOS[d]] & (SEC[SPOS[d]] >= 8) & (nbT[i] <= -8)
            if ok.any():
                q = int(np.argmax(ok)); plan[d] = (q, nbT[i, q])
        return plan
    real = freeze_plan("S3")
    rng = np.random.default_rng(1126 * 7 + int(cfg[3:]))
    for per in ("FIT", "CHECK", "T2"):
        k = sum(PER[d] == per for d in real)
        pool = [(i, d) for i, d in enumerate(bd) if PER[d] == per and (nbT[i] <= -8).any()]
        if not k or not pool:
            continue
        for j in rng.choice(len(pool), size=min(k, len(pool)), replace=False):
            i, d = pool[j]
            qs = np.flatnonzero(nbT[i] <= -8); q = int(rng.choice(qs)); plan[d] = (q, nbT[i, q])
    return plan


def run(cfg):
    blk, w = masks(cfg); plan = freeze_plan(cfg)
    rows = []
    for d, ix in GROUPS:
        fq = plan.get(d)
        fm = int(TMIN[fq[0]]) if fq else 10 ** 6
        r, nl, nbT = sim_day(ix, blk, w, fm)
        row = dict(date=d, per=PER[d], fire_q=fq[0] if fq else -1, fire_nb=fq[1] if fq else np.nan, nbT=nbT)
        for s in range(N):
            row[f"R{s}"] = r[s]; row[f"N{s}"] = nl[s]
        rows.append(row)
    out = pd.DataFrame(rows)
    out.to_parquet(OUT / f"day_{CTX}_{BOOKN}_{cfg}.parquet", index=False)
    return cfg, round(sum(out[f"R{s}"].sum() for s in range(N)), 1)


if __name__ == "__main__":
    print(CTX, BOOKN, "share blocked", {r: PSH[r].round(3).to_dict() for r in PSH}, flush=True)
    if "base" in CFGS:
        print(*run("base"), flush=True)
    rest = [c for c in CFGS if c != "base"]
    with Pool(int(__import__("os").environ.get("NPOOL", "2"))) as p:
        for c, tot in p.imap_unordered(run, rest):
            print(CTX, BOOKN, c, tot, flush=True)
