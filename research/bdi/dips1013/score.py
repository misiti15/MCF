"""dips1013 scoring: every configuration of PLAN.md (Part A 9,620, Part B 70,567) on the open history -> results.csv.
Educational only - not financial advice. The locked block is never loaded."""
from __future__ import annotations

import json
import time

import numpy as np
import pandas as pd

from configs import DEPTH, ENTRIES, EX_A, EX_B, GAPS, WIN, PartA, PartB, have_mask
from engine import HERE, Data, all_exits, fast_stats

T0 = time.time()
D = Data()
print("days", D.N, flush=True)
NET, CT = all_exits(D)
print("exits", round(time.time() - T0), flush=True)
rows = []
have = have_mask(D)


def add(cfg, part, d, k, exits, **kw):
    for ex in exits:
        rows.append({"cfg": f"{cfg}-{ex}", "part": part, "exit": ex, **kw, **fast_stats(D, NET, CT, ex, d, k)})


# ------------------------------------------------------------------------------------------------ Part A
A = PartA(D)
for (os_, L) in A.OSL:
    for tn in A.T:
        for fn in A.F:
            for wn in WIN:
                d, k = A.trades(os_, L, tn, fn, wn)
                add(f"A-{os_}-{L}-{tn}-{fn}-{wn}", "A", d, k, EX_A, os=os_, L=L, trig=tn, filt=fn, win=wn)
    print("A", os_, L, round(time.time() - T0), flush=True)
rng = np.random.default_rng(1013)
for wn, (lo, hi) in WIN.items():
    k = rng.integers(lo, hi + 1, D.N)
    d = np.flatnonzero(have)
    add(f"A-RANDOM-{wn}", "Ac", d, k[d], EX_A, trig="RANDOM", win=wn)
del A

# ------------------------------------------------------------------------------------------------ Part B
B = PartB(D)
for en in ENTRIES:
    FB = B.filters(en)
    ke = B.ENTRY[en][0]
    for ref in ("O", "PC", "B"):
        for unit, x in DEPTH:
            for gn in GAPS:
                base = B.base(en, ref, unit, x, gn)
                for fn, fm in FB.items():
                    d = np.flatnonzero(base & fm)
                    add(f"B-{ref}-{unit}{x}-{gn}-{en}-{fn}", "B", d, ke[d], EX_B, ref=ref, unit=unit, x=x, gapc=gn,
                        entry=en, filt=fn)
        print("B", en, ref, round(time.time() - T0), flush=True)
k = np.random.default_rng(1013).integers(2, 9, D.N)
d = np.flatnonzero(have)
add("B-RANDOM", "Bc", d, k[d], EX_B, entry="RANDOM")

res = pd.DataFrame(rows)
res.to_csv(HERE / "results.csv", index=False, float_format="%.5g")
cnt = {"A": int((res.part == "A").sum()), "Ac": int((res.part == "Ac").sum()), "B": int((res.part == "B").sum()),
       "Bc": int((res.part == "Bc").sum()), "total": int(len(res)), "seconds": round(time.time() - T0)}
json.dump(cnt, open(HERE / "counts.json", "w"), indent=1)
print(cnt)
