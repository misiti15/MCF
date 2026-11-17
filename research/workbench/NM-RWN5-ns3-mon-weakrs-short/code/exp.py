"""Mechanic NM-RWN5: screen of configs (each one part unless named combo) vs the parent, 2y (+ replay when built).
Usage: python exp.py <name> <json-file of {label: overrides}> [2y]. Educational only - not financial advice."""
import sys, json, pandas as pd, numpy as np
from sim import *
only2y = len(sys.argv) > 3
D = load(not only2y); C2, P2 = D["y2"]
tests = {"2y": (C2, P2, sorted(set(C2[C2.dow == 0].date)))}
if not only2y:
    RC, RP = D["rep"]; tests["replay"] = (RC, RP, sorted(set(RC.date)))
V = json.load(open(sys.argv[2]))
base = {k: trades(C, P, {}) for k, (C, P, _) in tests.items()}
rows = []
for name, v in {"parent": {}, **V}.items():
    if "extra" in v: v["extra"] = tuple(tuple(x) for x in v["extra"])
    if "dows" in v and v["dows"] is not None: v["dows"] = tuple(v["dows"])
    row = dict(cfg=name)
    for test, (C, P, days) in tests.items():
        t = base[test] if name == "parent" else trades(C, P, v)
        s = stats(t); p = paired(t, base[test], sorted(set(days) | set(t.date) if len(t) else days))
        pre = "y" if test == "2y" else "r"
        row.update({f"{pre}_n": s.get("n"), f"{pre}_avg": s.get("avg"), f"{pre}_wob": s.get("wobest"), f"{pre}_worst": s.get("worst"),
                    f"{pre}_tot": s.get("total"), f"{pre}_win": s.get("win"), f"{pre}_pd": p[0]})
        if test == "2y" and len(t):
            row.update(y_T=round(t[t.date <= "2025-12-31"].r.mean(), 3), y_V=round(t[t.date > "2025-12-31"].r.mean(), 3),
                       y_xA=round(t[t.date != "2025-04-14"].r.mean(), 3))
    rows.append(row)
R = pd.DataFrame(rows); R.to_csv(OUT + f"screen_{sys.argv[1]}.csv", index=False)
pd.set_option("display.width", 250); print(R.to_string())
