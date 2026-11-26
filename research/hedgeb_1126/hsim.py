"""HEDGE-B bench: squeeze_1125 minute book engine (Primary book rules, P4 / L3-OUT, latch BASE / LATCH-OPEN) with the
per-minute net beta E recorded, then the H8 / H4 SPY+IWM beta overlay (PREREG.md), the B8 block reference and the
shuffled-day placebo. Usage (cwd repo): python hsim.py W. Writes W/day_<ctx>_<book>_<cfg>.parquet.
Educational only - not financial advice."""
import sys
from multiprocessing import Pool
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parent))
from hedge_core import hedge  # noqa: E402

W = Path(sys.argv[1])
SETUPS = ["L3-gap-slope-fromopen-FD", "RW3-gapdn-rsi5pop-flowsell-short-FD",
          "RW5-heat30-flowsell-rsi5pop-gapdn-short-FD", "NM-ETF-late-dip-di-long"]
N = 4
LOCK = ("2024-11-01", "2025-02-28")
NPLAC, SEED = 20, 1126

C = pd.read_parquet(W / "cand.parquet")
d_ = C.date.astype(str)
assert not ((d_ >= LOCK[0]) & (d_ <= LOCK[1])).any(), "locked block row found"
PATH = np.load(W / "paths.npy", mmap_mode="r")
IDX = np.load(W / "idx.npy"); IDAYS = pd.read_csv(W / "idx_days.csv").iloc[:, 0].astype(str).tolist()
assert not any(LOCK[0] <= d <= LOCK[1] for d in IDAYS)
IPOS = {d: i for i, d in enumerate(IDAYS)}
IWB = pd.read_csv(W / "iwm_beta.csv", index_col=0).b.to_dict()
C["si"] = C.setup.map({s: i for i, s in enumerate(SETUPS)})
C = C.sort_values(["date", "em", "si", "symbol"], kind="mergesort").reset_index(drop=True)
C["b"] = C.side * C.beta * 0.01 * C.entry / C.risk
C["bi"] = C.side * C.beta_iwm * 0.01 * C.entry / C.risk
C["g"] = C.entry / C.risk                    # lot gross notional in R-dollars
DAYS = []
for d, g in C.groupby("date"):
    DAYS.append((d, g.per.iloc[0], {k: g[c].to_numpy(t) for k, c, t in (
        ("si", "si", int), ("side", "side", float), ("ent", "entry", float), ("risk", "risk", float), ("lc", "lcost", float),
        ("em", "em", int), ("xm", "xm", int), ("rr", "r", float), ("off", "off", int), ("n", "n", int), ("b", "b", float),
        ("bi", "bi", float), ("g", "g", float))} | {"sym": pd.factorize(g.symbol)[0]}))
RNG = np.random.default_rng(SEED)
NI = len(IDAYS)
PLAC = np.array([[(i + 1 + RNG.integers(NI - 1)) % NI for i in range(NI)] for _ in range(NPLAC)])   # other day, never self


def sim_day(G, keep, lo, bud, sh, H=20.0):
    si, sym, side, ent, risk, lc = G["si"], G["sym"], G["side"], G["ent"], G["risk"], G["lc"]
    em, xm, off, n, bb, bbi, gg = G["em"], G["xm"], G["off"], G["n"], G["b"], G["bi"], G["g"]
    shk = sh[si]; rr = G["rr"] - shk
    dur = np.maximum(xm - em, 1).astype(float)
    by_m = {}
    for k in np.flatnonzero(keep):
        by_m.setdefault(em[k], []).append(k)
    realized = np.zeros(N); nl = np.zeros(N, int); latched = np.zeros(N, bool); olat = np.zeros(N, bool)
    open_ = []; cnt = np.zeros(N, int); symcnt = {}
    halted = False; recent = [[] for _ in range(N)]
    trough = 0.0; nb = 0.0; blk = 0
    E = np.zeros(390); EI = np.zeros(390); ES = np.zeros((N, 390)); GR = np.zeros(390); OPN = np.zeros(390, bool)
    if not by_m:
        return realized, nl, trough, blk, E, EI, ES, GR, OPN
    m0, last = min(by_m), max(by_m)

    def realize(m):
        nonlocal open_, nb
        kp = []
        for k in open_:
            if xm[k] <= m:
                realized[si[k]] += rr[k]; cnt[si[k]] -= 1; symcnt[(si[k], sym[k])] -= 1; nb -= bb[k]
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
            if bud is not None and ((side[k] < 0 and nb <= -bud) or (side[k] > 0 and nb >= bud)):
                blk += 1; continue
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
            mk = side[o] * (c - ent[o]) / risk[o] - lc[o] - shk[o] * np.clip((m - em[o]) / dur[o], 0, 1)
            ps = realized + np.bincount(si[o], weights=mk, minlength=N)
            if 570 <= m < 960:
                q = m - 570
                E[q] = bb[o].sum(); EI[q] = bbi[o].sum(); ES[:, q] = np.bincount(si[o], weights=bb[o], minlength=N)
                GR[q] = gg[o].sum(); OPN[q] = True
        else:
            ps = realized.copy()
        if lo:
            olat |= ps <= -2.0 + 1e-12
        tot = ps.sum(); trough = min(trough, tot)
        if tot <= -H + 1e-12:
            halted = True
    for k in open_:
        realized[si[k]] += rr[k]
    return realized, nl, trough, blk, E, EI, ES, GR, OPN


def run(job):
    ctx, book, cfg, shift = job
    lineup, lat = ctx.split("_")
    lo = lat == "LO"; bud = 8.0 if cfg == "B8" else None
    sh = np.asarray(shift, float)
    rows = []
    for d, per, G in DAYS:
        keep = np.ones(len(G["si"]), bool) if lineup == "P4" else G["si"] != 0
        r, nl, tr, blk, E, EI, ES, GR, OPN = sim_day(G, keep, lo, bud, sh)
        i = IPOS.get(d)
        row = dict(date=d, per=per, trough=tr, blk=blk, R=r.sum(), lots=int(nl.sum()), Emax=np.abs(E).max(),
                   peak_lots_g=GR.max())
        for s in range(N):
            row[f"R{s}"] = r[s]; row[f"N{s}"] = nl[s]
        if i is not None:
            S, I = IDX[i, 0, 1:], IDX[i, 1, 1:]
            row["spy_oc"] = S[-1] / IDX[i, 0, 0] - 1
            biw = float(IWB.get(d, 1.2))
            if cfg == "REF":
                for B in (8.0, 4.0):
                    g_, c_, nr, tv, pv, pg, al = hedge(E, EI, ES, GR, OPN, S, I, biw, B)
                    t = f"H{int(B)}"
                    row.update({f"{t}_g": g_, f"{t}_c": c_, f"{t}_nreb": nr, f"{t}_tr": tv, f"{t}_pkv": pv, f"{t}_pkg": pg})
                    for s in range(N):
                        row[f"{t}_a{s}"] = al[s]
                for j in range(NPLAC):
                    q = PLAC[j, i]
                    g_, c_, *_ = hedge(E, EI, ES, GR, OPN, IDX[q, 0, 1:], IDX[q, 1, 1:], biw, 8.0)
                    row[f"PL{j}"] = g_ - c_
        rows.append(row)
    out = pd.DataFrame(rows)
    out.to_parquet(W / f"day_{ctx}_{book}_{cfg}.parquet", index=False)
    return job[:3], round(out.R.sum(), 1)


CTXS = ["P4_LO", "P4_BASE", "L3OUT_LO", "L3OUT_BASE"]
if __name__ == "__main__":
    print("days", len(DAYS), "index days", NI, "cands", len(C))
    with Pool(2) as p:
        for j, tot in p.imap_unordered(run, [(c, "RAW", cfg, [0.0] * N) for c in CTXS for cfg in ("REF", "B8")]):
            print(j, tot, flush=True)
    shifts = {}
    for c in CTXS:
        x = pd.read_parquet(W / f"day_{c}_RAW_REF.parquet")
        a = np.array([x[f"R{s}"].sum() / max(x[f"N{s}"].sum(), 1) for s in range(N)])
        shifts[c] = a; print(c, "avg R per lot by setup", a.round(4))
    pd.DataFrame(shifts, index=SETUPS).to_csv(W / "shifts.csv")
    jobs = [(c, "Z", cfg, list(shifts[c])) for c in CTXS for cfg in ("REF", "B8")]
    jobs += [(c, "P", "REF", list(shifts[c] - 0.10)) for c in CTXS]
    with Pool(2) as p:
        for j, tot in p.imap_unordered(run, jobs):
            print(j, tot, flush=True)
