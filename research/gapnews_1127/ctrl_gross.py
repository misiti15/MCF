"""GAPNEWS_1127 descriptive check: is the size-matched 'beats random names' gap a cost effect (wider stops) or selection?
Same control as score.py, on r_gross (before costs). Usage: python ctrl_gross.py WORK. Educational only - not financial advice."""
import json
import sys
import numpy as np
import score as S

x = S.load(); x, _ = S.add_k6(x); x, _, thr = S.add_rules(x)
o = {}
side = x.R8  # SA rule, FIT orientation +1 (score.py output)
for nm, t, pool in (("SA", S.mk(x, side, "x1", 0, x.k6rank <= 20), S.mk(x, side, "x1", 0, x.k6rank > 20)),
                    ("N2", None, None)):
    if nm == "N2":
        b = S.mk_bracket(x, "n2", 0); t, pool = b[b.index.isin(x.index[x.k6rank <= 20])], b[~b.index.isin(x.index[x.k6rank <= 20])]
    for p in ("CHECK", "T2"):
        a, q = t[t.per == p], pool[pool.per == p]
        o[f"{nm}|{p}"] = {"gross": S.ctrl_size(a, q, "r_gross"), "live": S.ctrl_size(a, q, "r_live"),
                          "risk_bps_list": round(float((a.risk / a.entry).median() * 1e4), 1),
                          "risk_bps_pool": round(float((q.risk / q.entry).median() * 1e4), 1)}
        print(nm, p, o[f"{nm}|{p}"], flush=True)
json.dump(o, open(S.H / "ctrl_gross.json", "w"), indent=1, default=float)
