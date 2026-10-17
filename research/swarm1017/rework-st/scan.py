"""Stages A-D of PLAN.md; every configuration is written to scan_all.csv.gz (empty ones too).
Educational only - not financial advice."""
import itertools
import sys
import time
from multiprocessing import Pool

import numpy as np
import pandas as pd

from common import (F, GEOMS, HERE, OPP, PARENT, PARENTS, PSIDE, SRCWIN, WINS, WM, apoints, col, core, score,
                    symday, barix)


def pick_idx(idx, s, g, refire=False):
    idx = idx[np.isfinite(col[f"p_{s}_{g}"][idx])]
    if not len(idx):
        return idx
    k = symday[idx]
    if not refire:
        return idx[np.r_[True, k[1:] != k[:-1]]]
    bi = barix[idx]
    newrun = np.r_[True, (k[1:] != k[:-1]) | (bi[1:] - bi[:-1] != 1)]
    rid = np.cumsum(newrun) - 1
    start = np.flatnonzero(newrun)
    off = np.arange(len(idx)) - start[rid]
    return idx[off % 2 == 0]


def work(p):
    rows = []
    t0 = time.time()
    sides = (PSIDE[p], OPP[PSIDE[p]])

    def run(stage, th, filt, side, geom, win, refire, idx):
        sel = idx[WM[win][idx]]
        ix = pick_idx(sel, side, geom, refire)
        rec = {"stage": stage, "parent": p, "th": repr(th), "filters": "+".join(filt), "side": side, "geom": geom,
               "win": win, "refire": refire}
        rec.update(score(ix, p, side, geom) if len(ix) else {"n_tr": 0, "n_va": 0, "n_all": 0})
        rows.append(rec)

    for th in apoints(p):                                          # Stage A
        idx = np.flatnonzero(core(p, th))
        for s, g, w in itertools.product(sides, GEOMS, WINS):
            run("A", th, (), s, g, w, False, idx)
    bidx = np.flatnonzero(core(p, PARENT[p]))
    FB = {f: v[bidx] for f, v in F.items()}
    for f in F:                                                    # Stage B + D
        idx = bidx[FB[f]]
        for s, g, w in itertools.product(sides, GEOMS, WINS):
            run("B", PARENT[p], (f,), s, g, w, False, idx)
            run("D", PARENT[p], (f,), s, g, w, True, idx)
    for f1, f2 in itertools.combinations(F, 2):                    # Stage C
        idx = bidx[FB[f1] & FB[f2]]
        for s, g, w in itertools.product(sides, GEOMS, (SRCWIN[p], "0950-1500")):
            run("C", PARENT[p], (f1, f2), s, g, w, False, idx)
    print(p, len(rows), round(time.time() - t0), flush=True)
    return rows


if __name__ == "__main__":
    with Pool(4) as pool:
        res = pool.map(work, PARENTS, chunksize=1)
    out = pd.DataFrame([r for rr in res for r in rr])
    out.to_csv(HERE / "scan_all.csv.gz", index=False, float_format="%.5g")
    print("configs", len(out), out.groupby("stage").size().to_dict(),
          out.assign(fam=out.parent.str[:2]).groupby("fam").size().to_dict())
