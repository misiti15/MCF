import numpy as np, pandas as pd
import load4 as L, sim4
bk = pd.read_pickle("C_books.pkl")
V = {"PARENT": {}, "C05 stop 1.25R": dict(dn=1.25), "C13 half +0.5R, half 1.5R, BE after 0.5R": dict(so_at=0.5, so_up=1.5, so_be=True)}
rows = []
for test, (c, g) in L.TESTS.items():
    for name, ch in V.items():
        v = dict(sim4.P, **ch); b = bk[(test, name)]
        rs = [sim4.random_entries(b, v, g, seed) for seed in range(5)]
        rr = np.array([x.r.mean() for x in rs])
        segs = {"ALL": None}
        row = dict(test=test, cfg=name, trades=len(b), signal_avg=b.r.mean(), random_avg_mean=rr.mean(), random_avg_min=rr.min(), random_avg_max=rr.max(),
                   edge_vs_random=b.r.mean() - rr.mean())
        if test == "2y":
            for sp in ("TRAIN", "VALID", "FWD"):
                row[f"signal_{sp}"] = b[b.date.map(L.split) == sp].r.mean()
                row[f"random_{sp}"] = np.mean([x[x.date.map(L.split) == sp].r.mean() for x in rs])
        rows.append(row); print(row, flush=True)
pd.DataFrame(rows).to_csv("C_random_entries.csv", index=False, float_format="%.4f")
