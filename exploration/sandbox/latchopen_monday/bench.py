"""LATCH-OPEN on the Monday roster, bench (CHECK 2025-10-01..2026-11-04 and T2 2023-01-03..2024-09-13; FIT dropped,
locked block 2024-11-01..2025-02-28 never read). Lots: bench10 candidates for the 4 Primary setups rebuilt tonight with
research/squeeze_1125/gen.py (sig1, walk1, t2) into WORK; filters and costs exactly as research/primshorts_1126/bench_build.py
(entry >= $5, shorts need ETB rate >= 0.9, LIVE-L cost on shorts from cells_live.json, NM-ETF keeps LR8 research).
Engine research/primshorts_1126/booksim.py unchanged (Primary book: 77 open, 30/setup, 3/setup/symbol, burst brake,
-2R per-setup latch, -20R halt on realised + open). 4 configs: roster A (RW3, RW5, NM-ETF) / roster B (A + L3) x latch
closed-only / closed + open. Writes OUT/lots.parquet (per-lot taken flags) for score.py.
cwd = repo checkout. Usage: python bench.py WORK ETB_PARQUET OUT. Educational only - not financial advice."""
import json, os, sys
from multiprocessing import Pool
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, str(Path.cwd())); sys.path.insert(0, str(Path.cwd() / "research/ultimate_1119/top10"))
P = str(Path.cwd() / "research/primshorts_1126"); sys.path.insert(0, P)
import bench10 as B  # noqa: E402
import calib_live as CL  # noqa: E402
from booksim import sim_day  # noqa: E402
import bench_build as BB  # noqa: E402  (module import is side-effect free apart from argv parsing below)
W, ETB, OUT = Path(sys.argv[1]), sys.argv[2], Path(sys.argv[3])
SETUPS = ["L3-gap-slope-fromopen-FD", "RW3-gapdn-rsi5pop-flowsell-short-FD", "RW5-heat30-flowsell-rsi5pop-gapdn-short-FD",
          "NM-ETF-late-dip-di-long"]
ROSTERS = {"A": [1, 2, 3], "B": [0, 1, 2, 3]}
LOCK = ("2024-11-01", "2025-02-28")


def build():
    x = pd.concat([pd.read_parquet(W / f"{f}.parquet") for f in ("trades_t1", "trades_t2")], ignore_index=True)
    x = x[x.setup.isin(SETUPS)].copy(); x["date"] = x.date.astype(str)
    x = B.add_r(x); x["per"] = x.date.map(BB.period); x = x[x.per.isin(["CHECK", "T2"])]
    BB.no_locked(x.date.unique())
    etb = pd.read_parquet(ETB).rate
    x = x[x.entry >= 5.0]; x = x[(x.side > 0) | x.symbol.map(etb).fillna(0).ge(0.9)]
    cells = json.load(open(P + "/cells_live.json"))
    kd = np.where(x.kind == 2, "target", np.where(x.kind == 1, "stop", "market"))
    x["r_live"] = np.where(x.side < 0, x.r_gross - CL.predict_R(cells, x.entry.to_numpy(), x.risk.to_numpy(), kd), x.r)
    t = x[["setup", "symbol", "date", "per", "side", "entry", "risk", "kind", "em", "xm", "r_gross", "r_live"]].reset_index(drop=True)
    print(t.groupby(["setup", "per"]).size().unstack(), flush=True)
    paths = {}
    with Pool(3) as p:
        for res in p.imap_unordered(BB.job, [(s, g) for s, g in t.groupby("symbol")], chunksize=8):
            for i, a in res:
                paths[i] = a
    print("missing paths", int((~t.index.isin(paths.keys())).sum()), flush=True)
    t = t[t.index.isin(paths.keys())].copy()
    off, n, arr, pos = [], [], [], 0
    for i in t.index:
        a = paths[i]; off.append(pos); n.append(len(a)); arr.append(a); pos += len(a)
    t["off"], t["n"] = off, n
    np.save(OUT / "paths.npy", np.concatenate(arr).astype(np.float32)); t.to_parquet(OUT / "cand.parquet", index=False)


def run(job):
    ros, lo_on = job
    C = pd.read_parquet(OUT / "cand.parquet"); PATH = np.load(OUT / "paths.npy", mmap_mode="r")
    C["si"] = C.setup.map({s: i for i, s in enumerate(SETUPS)})
    C = C[C.si.isin(ROSTERS[ros])].sort_values(["date", "em", "si", "symbol"], kind="mergesort").reset_index()
    out = []
    for d, g in C.groupby("date"):
        si = g.si.to_numpy(); side = g.side.to_numpy(float); ent = g.entry.to_numpy(float); risk = g.risk.to_numpy(float)
        rr = g.r_live.to_numpy(float); lc = (g.r_gross - g.r_live).to_numpy(float)
        em = g.em.to_numpy(int); xm = g.xm.to_numpy(int); off = g.off.to_numpy(int); n = g.n.to_numpy(int)

        def markf(o, m):
            j = np.clip(m - em[o], 0, n[o] - 1)
            return side[o] * (PATH[off[o] + j] - ent[o]) / risk[o] - lc[o]
        R, taken, tot, tr = sim_day(si, pd.factorize(g.symbol)[0], side, ent, risk, lc, em, xm, rr, markf, 4, np.ones(4),
                                    np.full(4, lo_on))
        out.append(pd.DataFrame(dict(per=g.per.iloc[0], roster=ros, lo=lo_on, date=d, lid=g["index"].to_numpy(),
                                     setup=g.setup.to_numpy(), r=rr, taken=taken)))
    return pd.concat(out)


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    if not (OUT / "cand.parquet").exists():
        build()
    with Pool(4) as p:
        L = p.map(run, [(r, lo) for r in ROSTERS for lo in (False, True)])
    L = pd.concat(L); L["key"] = L.per + " roster " + L.roster
    L.to_parquet(OUT / "lots.parquet", index=False)
    for k, g in L[L.taken].groupby(["key", "lo"]):
        print(k, round(g.r.sum(), 1), len(g))
    print("Educational only - not financial advice.")
