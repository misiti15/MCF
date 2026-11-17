"""Mechanic GEN-261023-09: screen. Every config scored with the identical engine on the 2-year backtest (train / valid /
all; isolated and with the live P14 cap of 50 open lots) and the replay of the live sessions; paired by day vs the parent;
one row = one config. Usage: python exp.py <name> <configs.json>. Educational only - not financial advice."""
import sys, json, pandas as pd, numpy as np
from sim import *
D = load(); C2, P2 = D["y2"]; RC, RP = D["rep"]
DAYS2 = sorted(set(C2.date)); DAYSR = sorted(set(RC.date))
V = json.load(open(sys.argv[2]))
base = {}
rows = []
for name, v in {"parent": {}, **V}.items():
    for k in ("extra", "conds"):
        if k in v: v[k] = tuple(tuple(x) for x in v[k])
    row = dict(cfg=name)
    for test, (C, P, days) in {"y": (C2, P2, DAYS2), "r": (RC, RP, DAYSR)}.items():
        for cap in (None, 50):
            t = trades(C, P, {**v, "conc": cap}); key = test + ("c" if cap else "")
            if name == "parent": base[key] = t
            s = stats(t); p = paired(t, base[key], days)
            row.update({f"{key}_n": s.get("n"), f"{key}_avg": s.get("avg"), f"{key}_wob": s.get("wobest"), f"{key}_worst": s.get("worst"),
                        f"{key}_tot": s.get("total"), f"{key}_win": s.get("win"), f"{key}_pd": p[0], f"{key}_pt": p[1]})
            if test == "y" and len(t):
                row[f"{key}_T"] = round(t[t.date <= "2025-12-31"].r.mean(), 3); row[f"{key}_V"] = round(t[t.date > "2025-12-31"].r.mean(), 3)
    rows.append(row); print(row, flush=True)
R = pd.DataFrame(rows); R.to_csv(OUT + f"screen_{sys.argv[1]}.csv", index=False)
print(R[["cfg", "y_n", "y_avg", "y_T", "y_V", "y_wob", "y_worst", "yc_avg", "yc_wob", "r_n", "r_avg", "r_wob", "r_worst", "rc_avg"]].to_string())
