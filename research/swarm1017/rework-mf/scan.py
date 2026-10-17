"""Scan the pre-declared grid (PLAN.md). Writes scan_all.csv (every configuration scored, counted).
Educational only - not financial advice."""
import itertools
import time

import pandas as pd

from common import *  # noqa: F401,F403
from common import F, PARENT, HGRID, BGRID, XGRID, PWIN, SG, WINS, WM, SCR, core, pick, score, lo_atr, hi_atr

rows = []
t0 = time.time()


def run(stage, parent, desc, m, combos, wins, refire=False, **kw):
    for w in wins:
        mw = m & WM[w]
        for s, g in combos:
            idx = pick(mw, s, g, refire)
            r = {"stage": stage, "parent": parent, "desc": desc, "side": s, "geom": g, "window": w, "refire": refire}
            r.update(kw)
            r.update(score(idx, s, g))
            rows.append(r)


for p in PARENT:
    # Stage A
    for h in HGRID[p]:
        for b in BGRID:
            for x in XGRID[p]:
                run("A", p, f"h{h} b{b} x{x}", core(p, h, b, x), SG, WINS, h=h, b=b, x=x)
    print("A", p, len(rows), round(time.time() - t0), flush=True)
    base = core(p, *PARENT[p])
    # Stage B + D
    for fn, fm in F.items():
        run("B", p, fn, base & fm, SG, WINS, f1=fn)
        run("D", p, fn, base & fm, SG, WINS, refire=True, f1=fn)
    print("BD", p, len(rows), round(time.time() - t0), flush=True)
    # Stage C
    for f1, f2 in itertools.combinations(F, 2):
        run("C", p, f"{f1}&{f2}", base & F[f1] & F[f2], SG, [PWIN[p], "0950-1500"] if PWIN[p] != "0950-1500" else ["0950-1500", "0950-1100"], f1=f1, f2=f2)
    print("C", p, len(rows), round(time.time() - t0), flush=True)

R = pd.DataFrame(rows)
R.to_csv(SCR / "scan_all.csv", index=False)
print("configs", len(R), "atr cuts", lo_atr, hi_atr)
