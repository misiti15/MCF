"""eu1103/preopen: does ANY of the 756 TRAIN gates carry over? Diagnostic only (nothing selected here): for every
configuration, its lift on VALID and live with the TRAIN threshold; Spearman of TRAIN lift vs VALID / live lift;
counts of gates admissible on TRAIN that also keep >= 70% / >= 90% and lift on VALID and live.
    python carryover.py <scratch>  -> research/bdi/eu1103/preopen/carryover.csv
Educational only - not financial advice."""
import sys
import numpy as np, pandas as pd
from scipy.stats import spearmanr
sys.path.insert(0, "/home/user/MCF/research/bdi/eu1103/preopen")
import gates as G

A = pd.read_csv(G.OUT / "all_gates.csv")
T = G.load_2y(); LV = G.load_live()
rows = []
for _, a in A.iterrows():
    o = {"group": a.group, "feature": a.feature, "cut": a.cut, "admissible": a.admissible, "train_lift": a.lift, "train_t": a.t_kd}
    for nm, df in (("valid", T[T.split == "VALID"]), ("live", LV)):
        d = df if a.group == "POOLED" else df[df.setup == a.group]
        if d.empty:
            continue
        w = d[a.feature].to_numpy(float)
        k = ~(w < a.thr) if a.cut.startswith("lo") else ~(w > a.thr)
        r = d.r.to_numpy(float)
        top = (d.r >= d.groupby("setup").r.transform(lambda s: s.quantile(0.9))).to_numpy()
        o[f"{nm}_keep"] = k.mean(); o[f"{nm}_top_keep"] = k[top].mean()
        o[f"{nm}_lift"] = r[k].mean() - r.mean() if k.any() else np.nan
    rows.append(o)
C = pd.DataFrame(rows)
C.to_csv(G.OUT / "carryover.csv", index=False, float_format="%.4f")
ad = C[C.admissible]
print("configs", len(C), "admissible on TRAIN", len(ad))
for nm in ("valid", "live"):
    x = C.dropna(subset=[f"{nm}_lift"])
    print(nm, "spearman train_lift vs lift: all %.3f p %.3g" % spearmanr(x.train_lift, x[f"{nm}_lift"]),
          "| admissible+train lift>0: n", int(((x.admissible) & (x.train_lift > 0)).sum()),
          "of which lift>0 here", int(((x.admissible) & (x.train_lift > 0) & (x[f"{nm}_lift"] > 0)).sum()),
          "and keep>=.7 & top>=.9 here", int(((x.admissible) & (x.train_lift > 0) & (x[f"{nm}_lift"] > 0) & (x[f"{nm}_keep"] >= .7) & (x[f"{nm}_top_keep"] >= .9)).sum()))
both = C[C.admissible & (C.train_lift > 0) & (C.valid_lift > 0) & (C.live_lift > 0) & (C.valid_keep >= .7) & (C.valid_top_keep >= .9) & (C.live_keep >= .7) & (C.live_top_keep >= .9)]
print("positive TRAIN + VALID + live with retention on all three:", len(both))
print(both.sort_values("valid_lift", ascending=False).head(15).to_string())
print("median VALID keep of TRAIN-admissible gates %.3f, live %.3f" % (ad.valid_keep.median(), ad.live_keep.median()))
