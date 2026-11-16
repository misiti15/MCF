"""Mechanic NM-ETF: one-part screen. Every config scored on 2y (train / valid / all) and the replay; counted.
Educational only - not financial advice."""
import sys, json, pandas as pd, numpy as np
from sim import *
D = load()
C2, P2 = D["y2"]; RC, RP = D["rep"]
DAYS2 = sorted(set(C2.date)); DAYSR = sorted(set(RC.date))
CF = json.loads(open(sys.argv[1]).read())
base2 = trades(C2, P2, {}); baseR = trades(RC, RP, {})
rows = []
for name, v in CF.items():
    v = {k: (tuple(tuple(e) for e in x) if k == "extra" else x) for k, x in v.items()}
    t2 = trades(C2, P2, v); tr = trades(RC, RP, v)
    s2 = stats(t2); sr = stats(tr)
    T = t2[t2.date <= "2025-12-31"].r; V = t2[t2.date > "2025-12-31"].r
    p2 = paired(t2, base2, DAYS2); pr = paired(tr, baseR, DAYSR)
    rows.append(dict(cfg=name, n2=s2["n"], T=round(T.mean(), 3), V=round(V.mean(), 3), nV=len(V), avg2=s2["avg"], wob2=s2["wobest"],
                     worst2=s2["worst"], win2=s2["win"], aw2=s2["avgw"], al2=s2["avgl"], dt2=p2[1], nR=sr.get("n"), avgR=sr.get("avg"),
                     wobR=sr.get("wobest"), worstR=sr.get("worst"), dtR=pr[1]))
    print(" ".join(f"{k}={v}" for k, v in rows[-1].items()), flush=True)
pd.DataFrame(rows).to_csv(OUT + sys.argv[1].replace(".json", ".csv"), index=False)
