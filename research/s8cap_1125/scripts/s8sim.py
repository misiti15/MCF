"""S8-CAP: direct minute-by-minute re-simulation of per-setup caps + SCALED-K4 (PLAN.md). Educational only - not financial advice.
Usage: python s8sim.py WORK P4|P9 BOOK(RAW|NEUTRAL|P10) CFG[,CFG...]"""
import sys
from multiprocessing import Pool
from pathlib import Path
import numpy as np
import pandas as pd

W = Path(sys.argv[1]); LINE = sys.argv[2]; BOOK = sys.argv[3]; CFGS = sys.argv[4].split(",")
P4 = ["L3-gap-slope-fromopen-FD", "RW3-gapdn-rsi5pop-flowsell-short-FD", "RW5-heat30-flowsell-rsi5pop-gapdn-short-FD",
      "NM-ETF-late-dip-di-long"]
EXTRA = ["L3-gap-slope-lowdist-FD", "L3-gap-slope-rsi5hi-FD", "RW7-gapdn-bounce-early-short-FD", "RW6-ns2-up3-short-FD",
         "GEN-261029-06-EMAdChgge0p092-DayRngVsPrevle0p61-LATE-QQQltm0p3-t1s1-short"]
SETUPS = P4 + (EXTRA if LINE == "P9" else [])
N = len(SETUPS)
# config table: latch, cap kind/level, account layer
CFG = {"NOW": (True, None, False), "REF": (True, None, True), "K4N": (False, None, True)}
for L in (6, 8, 10):
    CFG[f"C{L}L"] = (True, float(L), True); CFG[f"C{L}N"] = (False, float(L), True)
CFG["CSL"] = (True, "S", True); CFG["CSN"] = (False, "S", True)

C = pd.read_parquet(W / "cand.parquet")
C = C[C.setup.isin(SETUPS)].copy()
PATH = np.load(W / "paths.npy", mmap_mode="r")
C["si"] = C.setup.map({s: i for i, s in enumerate(SETUPS)})
C = C.sort_values(["date", "em", "si", "symbol"], kind="mergesort").reset_index(drop=True)
SHIFT = np.zeros(N)
if BOOK != "RAW":
    a = pd.read_csv(W / f"avg_{LINE}.csv").set_index("setup").a.reindex(SETUPS).fillna(0).to_numpy()
    SHIFT = a if BOOK == "NEUTRAL" else a - 0.10
DAYS = []
for d, g in C.groupby("date"):
    sym_codes = pd.factorize(g.symbol)[0]
    DAYS.append((d, dict(si=g.si.to_numpy(), sym=sym_codes, side=g.side.to_numpy(float), ent=g.entry.to_numpy(float),
                         risk=g.risk.to_numpy(float), tier=g.tier.to_numpy(float), ec=g.ecost.to_numpy(float),
                         bo=g.borrow.to_numpy(float), em=g.em.to_numpy(int), xm=g.xm.to_numpy(int), rr=g.r.to_numpy(float),
                         off=g.off.to_numpy(int), n=g.n.to_numpy(int))))


def sim_day(G, latch, Lcap, X, H):
    si, sym, side, ent, risk, tier, ec, bo = G["si"], G["sym"], G["side"], G["ent"], G["risk"], G["tier"], G["ec"], G["bo"]
    em, xm, off, n = G["em"], G["xm"], G["off"], G["n"]
    sh = SHIFT[si]
    rr = G["rr"] - sh
    dur = np.maximum(xm - em, 1).astype(float)
    by_m = {}
    for k in range(len(si)):
        by_m.setdefault(em[k], []).append(k)
    realized = np.zeros(N); nl = np.zeros(N, int)
    open_ = []; cnt = np.zeros(N, int); symcnt = {}
    capped = np.zeros(N, bool); capm = np.full(N, -1)
    halted = stopped = False; halt_m = stop_m = -1
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
        for k in by_m.get(m, ()):
            realize(m)
            s = si[k]
            if halted or stopped or capped[s]:
                continue
            if latch and realized[s] <= -2.0 + 1e-12:
                continue
            if len(open_) >= 77 or cnt[s] >= 30 or symcnt.get((s, sym[k]), 0) >= 3:
                continue
            recent[s] = [t for t in recent[s] if t > m - 10]
            if len(recent[s]) >= 30:
                continue
            recent[s].append(m); nl[s] += 1; open_.append(k); cnt[s] += 1
            symcnt[(s, sym[k])] = symcnt.get((s, sym[k]), 0) + 1
        realize(m)
        if open_:
            o = np.array(open_)
            j = np.minimum(m - em[o], n[o] - 1)
            c = np.where(n[o] > 0, PATH[off[o] + np.maximum(j, 0)], ent[o])
            mk = (side[o] * (c - ent[o]) - tier[o] * (ec[o] + 0.01 + c * 1e-4) - bo[o]) / risk[o]
            mk = mk - sh[o] * np.clip((m - em[o]) / dur[o], 0, 1)
            ps = realized + np.bincount(si[o], weights=mk, minlength=N)
        else:
            o = np.zeros(0, int); mk = np.zeros(0); ps = realized.copy()
        if Lcap is not None:
            hit = (~capped) & (ps <= -Lcap + 1e-12)
            if hit.any():
                for s in np.flatnonzero(hit):
                    capped[s] = True; capm[s] = m
                    sel = si[o] == s
                    realized[s] += mk[sel].sum()
                    for k in o[sel]:
                        cnt[s] -= 1; symcnt[(s, sym[k])] -= 1
                keep = ~capped[si[o]]
                open_ = list(o[keep]); mk = mk[keep]; o = o[keep]
        tot = ps.sum()
        trough = min(trough, tot)
        if not halted and tot <= -H + 1e-12:
            halted = True; halt_m = m
        if X is not None and not stopped and tot <= -X + 1e-12:
            stopped = True; stop_m = m
            for k, v in zip(o, mk):
                realized[si[k]] += v
            open_ = []
            break
    for k in open_:
        realized[si[k]] += rr[k]
    return realized, nl, capm, halt_m, stop_m, trough


def run(cfgname):
    latch, cap, acct = CFG[cfgname]
    D = [d for d, _ in DAYS]
    dts = pd.to_datetime(pd.Series(D))
    iso = dts.dt.isocalendar()
    wk = (iso.year.astype(str) + "-" + iso.week.astype(str).str.zfill(2)).to_numpy()
    first = {}
    for i, w in enumerate(wk):
        first.setdefault(w, i)
    fin = np.zeros((len(D), N)); lots = np.zeros((len(D), N), int)
    rows = []
    cal = {}
    for i, (d, G) in enumerate(DAYS):
        j = first[wk[i]]
        if j not in cal:
            if j >= 120:
                tot = fin[max(0, j - 250):j].sum(1)
                X = float(np.clip(4 * tot.std(ddof=1), 2.5 * N, 8 * N))
                Ls = np.full(N, 8.0)
                for s in range(N):
                    act = lots[max(0, j - 250):j, s] > 0
                    if act.sum() >= 20:
                        Ls[s] = float(np.clip(1.5 * fin[max(0, j - 250):j, s][act].std(ddof=1), 4, 12))
                cal[j] = (X, Ls, True)
            else:
                cal[j] = (None, np.full(N, 8.0), False)
        X, Ls, scored = cal[j]
        if not acct:
            Xu, H = None, 20.0
        else:
            Xu, H = X, (max(20.0, 0.6 * X) if X is not None else 20.0)
        Lc = None if cap is None else (Ls if cap == "S" else np.full(N, cap))
        r, nl, capm, hm, sm, tr = sim_day(G, latch, Lc, Xu, H)
        fin[i] = r; lots[i] = nl
        row = dict(date=d, scored=scored, X=Xu if Xu is not None else np.nan, H=H, halt_m=hm, stop_m=sm, trough=tr)
        for s in range(N):
            row[f"R{s}"] = r[s]; row[f"N{s}"] = nl[s]; row[f"M{s}"] = capm[s]; row[f"L{s}"] = Lc[s] if Lc is not None else np.nan
        rows.append(row)
    out = pd.DataFrame(rows)
    out.to_parquet(W / f"day_{LINE}_{BOOK}_{cfgname}.parquet", index=False)
    sc = out[out.scored]
    return cfgname, round(sum(sc[f"R{s}"].sum() for s in range(N)), 1)


if __name__ == "__main__":
    with Pool(min(4, len(CFGS))) as p:
        for c, tot in p.imap_unordered(run, CFGS):
            print(LINE, BOOK, c, tot, flush=True)
