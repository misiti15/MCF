"""Mechanic GEN-261023-09: 2-year pre-screen, isolated AND with the live P14 cap (50 open lots per setup).
Educational only - not financial advice."""
import sys, json, pickle, pandas as pd, numpy as np
from sim import *
C = pd.read_parquet(OUT + "cand2y.parquet"); P = pickle.load(open(OUT + "paths2y.pkl", "rb"))
V = json.load(open(sys.argv[1]))
for name, v in {"parent": {}, **V}.items():
    for k in ("extra", "conds"):
        if k in v: v[k] = tuple(tuple(x) for x in v[k])
    t = trades(C, P, v); s = stats(t); tc = trades(C, P, {**v, "conc": 50}); sc = stats(tc)
    f = lambda t, a, b: t[(t.date >= a) & (t.date <= b)].r.mean()
    print(f"{name:34s} ISO n={s['n']:5d} avg={s['avg']:+.3f} T={f(t,'2000','2025-12-31'):+.3f} V={f(t,'2026','2027'):+.3f} wob={s['wobest']:+.3f} worst={s['worst']:6.1f} | CAP50 n={sc['n']:5d} avg={sc['avg']:+.3f} T={f(tc,'2000','2025-12-31'):+.3f} V={f(tc,'2026','2027'):+.3f} wob={sc['wobest']:+.3f} worst={sc['worst']:6.1f}", flush=True)
