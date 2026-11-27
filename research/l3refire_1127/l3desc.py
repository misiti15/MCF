"""L3REFIRE-1127 descriptive: on the E4 keep run (BASE, LO), L3 lots taken first in a name that day vs repeat lots,
avg R (LIVE-L), per period. Usage (cwd repo): python research/l3refire_1127/l3desc.py W. Educational only."""
import json
import sys
import numpy as np
sys.path.insert(0, "research/l3refire_1127")
import e4l3 as L  # noqa: E402
C, DAYS, ST, PATH, A = L.load(sys.argv[1])
out = {}
for cx, lo in (("BASE", False), ("LO", True)):
    _, _, TK = L.run(A, ST, PATH, np.arange(len(DAYS)), np.ones(len(C), bool), lo)
    x = C[TK & (A["si"] == 0)].sort_values(["date", "em"]).copy()
    x["rep"] = x.groupby(["date", "symbol"]).cumcount() > 0
    for p in ("FIT", "CHECK", "T2"):
        for nm, g in (("first", x[(x.per == p) & ~x.rep]), ("repeat", x[(x.per == p) & x.rep])):
            dd = g.groupby("date").r.sum()
            out[f"{cx}|{p}|{nm}"] = dict(n=int(len(g)), avg=round(float(g.r.mean()), 4),
                                         avg_wo_best_day=round(float((g.r.sum() - dd.max()) / max(len(g) - (g.date == dd.idxmax()).sum(), 1)), 4),
                                         stop_share=round(float((g.kind == 1).mean()), 3))
print(json.dumps(out, indent=1))
