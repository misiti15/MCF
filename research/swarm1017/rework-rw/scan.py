"""Scan the pre-declared grid (PLAN.md). Writes scan_all.csv.gz to scratch (every configuration scored, counted).
Educational only - not financial advice."""
import itertools
import time

import numpy as np
import pandas as pd

from common import (CWIN, F, GRIDS, LIVE_REFIRE, PARENT, SCR, SG, W5, WM, pick, score)

rows = []
t0 = time.time()


def run(stage, parent, desc, base, wins, combos=SG, refire=None, **kw):
    for w in wins:
        rr = np.flatnonzero(base & WM[w]) if base.dtype == bool and len(base) == len(WM[w]) else None
        for s, g in combos:
            idx = pick(rr, s, g, refire)
            r = {"stage": stage, "parent": parent, "desc": desc, "side": s, "geom": g, "window": w,
                 "refire": refire if refire is not None else 0}
            r.update(kw)
            r.update(score(idx, s, g))
            rows.append(r)


# parents at their live setting (short t1s1 full day)
for p, f in PARENT.items():
    run("P", p, "parent", f(), ["0950-1500"], [("short", "t1s1")], refire=LIVE_REFIRE[p])
    run("P0", p, "parent first-signal", f(), ["0950-1500"], [("short", "t1s1")])  # diagnostic, counted
print("P", len(rows), flush=True)

# Stage A
for gname, (fn, axes) in GRIDS.items():
    wins = W5 + (["1110-1500"] if gname == "G-EXH" else [])
    for combo in itertools.product(*axes):
        m = fn(*combo)
        run("A", gname, "|".join(map(str, combo)), m, wins, **{f"a{i}": str(v) for i, v in enumerate(combo)})
    print("A", gname, len(rows), round(time.time() - t0), flush=True)

# Stage B, D, C on parent-restricted rows
for p, f in PARENT.items():
    base = f() & WM["0950-1500"]
    B = np.flatnonzero(base)
    Fs = {k: v[B] for k, v in F.items()}
    Ws = {w: WM[w][B] for w in W5}

    def runr(stage, desc, sub, wins, refire=None, **kw):
        for w in wins:
            rr = B[sub & Ws[w]]
            for s, g in SG:
                idx = pick(rr, s, g, refire)
                r = {"stage": stage, "parent": p, "desc": desc, "side": s, "geom": g, "window": w,
                     "refire": refire if refire is not None else 0}
                r.update(kw)
                r.update(score(idx, s, g))
                rows.append(r)

    for fn_, fm in Fs.items():
        runr("B", fn_, fm, W5, f1=fn_)
        runr("D", fn_, fm, W5, refire=1, f1=fn_)
    for f1, f2 in itertools.combinations(Fs, 2):
        runr("C", f"{f1}&{f2}", Fs[f1] & Fs[f2], CWIN[p], f1=f1, f2=f2)
    print("BCD", p, len(B), len(rows), round(time.time() - t0), flush=True)

R = pd.DataFrame(rows)
R.to_csv(SCR / "scan_all.csv.gz", index=False)
print("configs", len(R), R.stage.value_counts().to_dict())
