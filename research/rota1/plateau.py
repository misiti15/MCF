"""ROTA1: plateau check on wf_grid.csv (one-notch neighbours). Educational only — not financial advice.

    python research/rota1/plateau.py
"""
from pathlib import Path

import numpy as np
import pandas as pd

OUT = Path(__file__).resolve().parent
G = {"h": [3, 5, 7], "L": [40, 60, 90], "score": ["S1", "S2", "S3"], "m": [0.05, 0.10, 0.20],
     "max_swaps": [1, 2], "k": [6, 8, 10], "flag": [0, 1]}
d = pd.read_csv(OUT / "wf_grid.csv")
g = d[d.score != "LIGHT"].copy()
for c in ("L", "max_swaps", "k", "flag"):
    g[c] = g[c].astype(int)
key = lambda r: tuple(r[c] for c in G)
idx = {key(r): r for _, r in g.iterrows()}
rows = []
for kk, r in idx.items():
    nb = []
    for j, c in enumerate(G):
        vals = G[c]
        p = vals.index(kk[j])
        opts = vals if c == "score" else [vals[q] for q in (p - 1, p + 1) if 0 <= q < len(vals)]
        for v in opts:
            if v == kk[j]:
                continue
            k2 = list(kk); k2[j] = v
            nb.append(idx[tuple(k2)])
    nb = pd.DataFrame(nb)
    rows.append({**dict(zip(G, kk)), "TRAIN": r.TRAIN_mean, "VALID": r.VALID_mean, "FWD": r.FWD_mean, "TV_t": r.TV_t,
                 "nb": len(nb), "nb_pos_both": int(((nb.TRAIN_mean > 0) & (nb.VALID_mean > 0)).sum()),
                 "nb_med_t": nb.TV_t.median(), "nb_min_t": nb.TV_t.min()})
p = pd.DataFrame(rows)
p["plateau_ok"] = (p.TRAIN > 0) & (p.VALID > 0) & (p.nb_pos_both == p.nb) & (p.nb_med_t >= 1.5)
p.round(4).to_csv(OUT / "plateau.csv", index=False)
print("configs on a plateau (pos both, all neighbours pos both, neighbour median t >= 1.5):", int(p.plateau_ok.sum()))
print(p.sort_values(["plateau_ok", "nb_med_t"], ascending=False).head(15).round(3).to_string(index=False))
