"""Stages A-D of PLAN.md; every configuration is written to scan_all.csv.gz (empty ones too).
Educational only - not financial advice."""
import itertools
import time

import numpy as np
import pandas as pd

from common import F, GEOMS, GRID, HERE, OPP, PARENT, PSIDE, PWIN, WINS, WM, core, pick, score

rows = []
t0 = time.time()


def run(stage, p, th, filt, side, geom, win, refire, m):
    idx = pick(m & WM[win], side, geom, refire)
    rec = {"stage": stage, "parent": p, "th": str(th), "filters": "+".join(filt), "side": side, "geom": geom,
           "win": win, "refire": refire}
    rec.update(score(idx, side, geom) if len(idx) else {"n_tr": 0, "n_va": 0, "n_all": 0})
    rows.append(rec)


for p in GRID:
    sides = (PSIDE[p], OPP[PSIDE[p]])
    for th in GRID[p]:                                   # Stage A
        m = core(p, th)
        for s, g, w in itertools.product(sides, GEOMS, WINS):
            run("A", p, th, (), s, g, w, False, m)
    base = core(p, PARENT[p])
    for f in F:                                          # Stage B + D
        m = base & F[f]
        for s, g, w in itertools.product(sides, GEOMS, WINS):
            run("B", p, PARENT[p], (f,), s, g, w, False, m)
            run("D", p, PARENT[p], (f,), s, g, w, True, m)
    for f1, f2 in itertools.combinations(F, 2):          # Stage C
        m = base & F[f1] & F[f2]
        for s, g, w in itertools.product(sides, GEOMS, (PWIN[p], "0950-1500")):
            run("C", p, PARENT[p], (f1, f2), s, g, w, False, m)
    print(p, len(rows), round(time.time() - t0), flush=True)

out = pd.DataFrame(rows)
out.to_csv(HERE / "scan_all.csv.gz", index=False, float_format="%.5g")
print("configs", len(out))
