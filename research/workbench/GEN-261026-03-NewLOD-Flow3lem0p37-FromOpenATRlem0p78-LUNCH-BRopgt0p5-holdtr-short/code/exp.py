"""Mechanic GEN-261026-03: screen of configs (each one part unless named combo) on BOTH tests vs the parent.
Usage: python exp.py <name> <json-file of {label: overrides}>. Educational only - not financial advice."""
import sys, json, pandas as pd, numpy as np
from sim import *
D = load(); C2, P2 = D["y2"]; RC, RP = D["rep"]
DAYS2 = sorted(set(C2.date)); DAYSR = sorted(set(RC.date))
V = json.load(open(sys.argv[2]))
base = {"2y": trades(C2, P2, {}), "replay": trades(RC, RP, {})}
rows = []
for name, v in {"parent": {}, **V}.items():
    if "extra" in v: v["extra"] = tuple(tuple(x) for x in v["extra"])
    row = dict(cfg=name)
    for test, (C, P, days) in {"2y": (C2, P2, DAYS2), "replay": (RC, RP, DAYSR)}.items():
        t = base[test] if name == "parent" else trades(C, P, v)
        s = stats(t); p = paired(t, base[test], days)
        sp = t[t.date <= "2025-12-31"].r.mean() if test == "2y" and len(t) else np.nan
        sv = t[t.date > "2025-12-31"].r.mean() if test == "2y" and len(t) else np.nan
        pre = "y" if test == "2y" else "r"
        row.update({f"{pre}_n": s.get("n"), f"{pre}_avg": s.get("avg"), f"{pre}_wob": s.get("wobest"), f"{pre}_worst": s.get("worst"),
                    f"{pre}_tot": s.get("total"), f"{pre}_win": s.get("win"), f"{pre}_pd": p[0]})
        if test == "2y": row.update(y_T=round(sp, 3), y_V=round(sv, 3))
    rows.append(row); print(row, flush=True)
R = pd.DataFrame(rows); R.to_csv(OUT + f"screen_{sys.argv[1]}.csv", index=False); print(R.to_string())
