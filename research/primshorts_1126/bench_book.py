"""PRIMSHORTS-1126 lineup options on the bench10 lots (bench_build.py OUT): Primary book (booksim.py) with today's 4
setups; options a keep / b L3 out / c L3 half size / d L3 latch counts open R; each with LATCH-OPEN off and on (LO on
for every setup); costs LIVE-L (shorts) and LR8 research. Open marks = 1-min close path less the lot's full cost.
Usage: python bench_book.py OUT. Educational only - not financial advice."""
import os, sys
from multiprocessing import Pool
from pathlib import Path
import numpy as np, pandas as pd
H = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, H)
from booksim import sim_day  # noqa: E402
OUT = Path(sys.argv[1])
SETUPS = ["L3-gap-slope-fromopen-FD", "RW3-gapdn-rsi5pop-flowsell-short-FD", "RW5-heat30-flowsell-rsi5pop-gapdn-short-FD",
          "NM-ETF-late-dip-di-long"]
N = 4
OPTS = {"a_keep": (1.0, False), "b_L3_out": (0.0, False), "c_L3_half": (0.5, False), "d_L3_latchopen": (1.0, True)}
C = pd.read_parquet(OUT / "cand.parquet")
d_ = C.date.astype(str); assert not ((d_ >= "2024-11-01") & (d_ <= "2025-02-28")).any()
PATH = np.load(OUT / "paths.npy", mmap_mode="r")
C["si"] = C.setup.map({s: i for i, s in enumerate(SETUPS)})
C = C.sort_values(["date", "em", "si", "symbol"], kind="mergesort").reset_index(drop=True)
DAYS = [(d, g) for d, g in C.groupby("date")]
PER = C.groupby("date").per.first().to_dict()


def run(job):
    cost, lo_all, opt = job
    wl3, lol3 = OPTS[opt]
    w = np.array([wl3, 1, 1, 1.0]); lo = np.array([lo_all or lol3, lo_all, lo_all, lo_all])
    rows = []
    for d, g in DAYS:
        if wl3 == 0.0:
            g = g[g.si != 0]
        if not len(g):
            rows.append(dict(date=d, per=PER[d], R=0.0, trough=0.0)); continue
        si = g.si.to_numpy(); side = g.side.to_numpy(float); ent = g.entry.to_numpy(float); risk = g.risk.to_numpy(float)
        rr = g[f"r_{cost}"].to_numpy(float); lc = (g.r_gross - g[f"r_{cost}"]).to_numpy(float)
        em = g.em.to_numpy(int); xm = g.xm.to_numpy(int); off = g.off.to_numpy(int); n = g.n.to_numpy(int)

        def markf(o, m):
            j = np.clip(m - em[o], 0, n[o] - 1)
            c = PATH[off[o] + j]
            return side[o] * (c - ent[o]) / risk[o] - lc[o]
        R, taken, tot, tr = sim_day(si, pd.factorize(g.symbol)[0], side, ent, risk, lc, em, xm, rr, markf, N, w, lo)
        row = dict(date=d, per=g.per.iloc[0], R=tot, trough=tr)
        for s in range(N):
            row[f"R{s}"] = R[s] * w[s]; row[f"N{s}"] = int(taken[si == s].sum())
        rows.append(row)
    out = pd.DataFrame(rows).fillna(0.0)
    out.to_parquet(OUT / f"book_{cost}_{'LO' if lo_all else 'BASE'}_{opt}.parquet", index=False)
    return job, round(out.R.sum(), 1)


if __name__ == "__main__":
    jobs = [(c, lo, o) for c in ("live", "lr8") for lo in (False, True) for o in OPTS]
    with Pool(3) as p:
        for j, tot in p.imap_unordered(run, jobs):
            print(j, tot, flush=True)
