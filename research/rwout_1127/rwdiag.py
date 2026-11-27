"""RWOUT-1127 post-hoc diagnostics (not configs; added after scoring, disclosed in REPORT.md):
(1) lots taken by the size-matched random draws (20 draws, seed 1127) vs the config - the random control is matched on
removed lots, but freed caps refill, so random draws keep far more exposure; (2) each config vs its exposure-matched
constant cut (day-paired dR and t) from rwrun.py day files. Usage (cwd repo): python research/rwout_1127/rwdiag.py W OUTDIR.
Educational only - not financial advice."""
import json
import sys
from pathlib import Path
import numpy as np
import pandas as pd

sys.path.insert(0, "research/rwout_1127")
import rwrun as R  # noqa: E402  (loads W from argv; locked block asserted there)

E, A, OUT = R.E, R.A, Path(sys.argv[2])
res = {"random_lots": [], "vs_cut": []}
for cx, lo in R.CTX.items():
    Rref, Nref, TK = E.run(A, R.ST, R.PATH, R.ALL, np.ones(len(R.C), bool), lo)
    for cfg, rm in R.CFG.items():
        mask = ~np.isin(R.SI, rm); g = np.random.default_rng(1127)
        a = pd.read_parquet(OUT / f"day_{cx}_{cfg}.parquet"); b = pd.read_parquet(OUT / f"day_{cx}_{cfg}_CUT.parquet")
        for p in ("CHECK", "T2"):
            ix = np.flatnonzero(R.PER == p); inp = R.DPC == p
            n = int((TK & inp & ~mask).sum()); pool = np.flatnonzero(TK & R.SHORT & inp)
            _, Nc, _ = E.run(A, R.ST, R.PATH, ix, mask, lo)
            L = []
            for _ in range(20):
                kr = np.ones(len(R.C), bool); kr[g.choice(pool, min(n, len(pool)), replace=False)] = False
                L.append(int(E.run(A, R.ST, R.PATH, ix, kr, lo)[1].sum()))
            res["random_lots"].append(dict(ctx=cx, cfg=cfg, per=p, keep=int(Nref[ix].sum()), cfg_lots=int(Nc.sum()),
                                           random_mean_lots=float(np.mean(L))))
            m = a.per == p; d = (a[E.SETUPS].sum(axis=1) - b[E.SETUPS].sum(axis=1))[m]
            res["vs_cut"].append(dict(ctx=cx, cfg=cfg, per=p, dR_vs_cut=float(d.mean()),
                                      t=float(d.mean() / (d.std(ddof=1) / np.sqrt(len(d))))))
json.dump(res, open(OUT / "diag.json", "w"), indent=1)
for k in res:
    print(pd.DataFrame(res[k]).round(2).to_string(index=False))
