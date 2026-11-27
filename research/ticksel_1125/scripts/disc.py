"""TICKSEL discovery on FIT only -> fit_tables.csv + configs.json (selection rule from PREREG.md). Educational only."""
import json, sys
import numpy as np, pandas as pd
sys.path.insert(0, "/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/ticksel")
from lib2 import *
T = "/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/ticksel/"
B = pd.read_parquet(T + "bk_t1.parquet")
F = B[(B.half == "fit") & ~B.rnd]
assert F.date.max() <= "2025-09-30"
TRAITS = ["price", "adv20", "atrp", "beta", "gap", "ret1", "ret5", "rvol1", "sector", "etf", "levinv", "spread", "etb"]
SINGLES = {"RW6", "NMETF", "GEN06"}
rows, cuts = [], {}
for fam, G in F.groupby("fam"):
    for tr in TRAITS:
        if tr == "etb" and G.side.iloc[0] > 0: continue
        c = cuts_for(G, tr, 5) if tr in QTRAITS else (cuts_for(G, "spread", 3) if tr == "spread" else [])
        cuts[f"{fam}|{tr}"] = c
        bk = bucket(G, tr, c)
        for bv in sorted(pd.unique(bk)):
            ind = (bk == bv)
            if ind.sum() < 10: continue
            d1, t1 = diff_t(G.r, ind, G.date)
            d2, t2 = diff_t(G.r_adj, ind, G.date)
            sm = summ(G.r[ind], G.date[ind])
            rows.append(dict(fam=fam, trait=tr, bucket=bv, n=int(ind.sum()), share=ind.mean(), avg=sm["avg"],
                             avg_adj=G.r_adj[ind].mean(), rest=G.r[~ind].mean(), diff=d1, t=t1, diff_adj=d2, t_adj=t2,
                             wobd=sm["wobd"], days=sm["days"]))
X = pd.DataFrame(rows)
X.to_csv(T + "fit_tables.csv", index=False)
# exclusion candidates
nmin = np.where(X.fam.isin(SINGLES), 60, 150)
ex = X[(X.n >= nmin) & (X.share <= 0.25) & (X["diff"] <= -0.10) & (X.diff_adj <= -0.10) & (X.t <= -2.5) & (X.t_adj <= -2.5)
       & (X.bucket != "na")].sort_values("t")
print("EXCLUSION candidates (FIT):\n", ex.head(20).to_string())
# tilt candidates: monotone quintile traits, Q5 vs Q1
tl = []
for (fam, tr), g in X[X.trait.isin(QTRAITS + ["price"]) & (X.bucket != "na")].groupby(["fam", "trait"]):
    if fam in SINGLES: continue
    g = g.sort_values("bucket") if tr != "price" else g.set_index("bucket").reindex(["<10", "10-20", "20-50", "50-100", ">=100"]).dropna(subset=["n"]).reset_index()
    if len(g) < 3: continue
    rho = pd.Series(g.avg.values).corr(pd.Series(range(len(g))), method="spearman")
    G = F[F.fam == fam]
    bk = bucket(G, tr, cuts[f"{fam}|{tr}"])
    lo, hi = g.bucket.iloc[0], g.bucket.iloc[-1]
    sub = bk.isin([lo, hi]) if hasattr(bk, "isin") else np.isin(bk, [lo, hi])
    d, t = diff_t(G.r[sub], (bk[sub] == hi), G.date[sub])
    da, ta = diff_t(G.r_adj[sub], (bk[sub] == hi), G.date[sub])
    tl.append(dict(fam=fam, trait=tr, lo=lo, hi=hi, rho=rho, diff=d, t=t, diff_adj=da, t_adj=ta))
TL = pd.DataFrame(tl)
TL["score"] = TL.t.abs()
tsel = TL[(TL.t.abs() >= 2.5) & (TL.t_adj.abs() >= 2.5) & (TL.rho.abs() >= 0.7) & (np.sign(TL.rho) == np.sign(TL.t))].sort_values("score", ascending=False)
print("TILT table (FIT):\n", TL.sort_values("score", ascending=False).to_string())
cfg = {"cuts": cuts, "X": [], "W": []}
for i, r in enumerate(ex.head(8).itertuples(), 1):
    cfg["X"].append(dict(id=f"X{i}", fam=r.fam, trait=r.trait, bucket=r.bucket, fit_n=r.n, fit_share=r.share,
                         fit_avg=r.avg, fit_diff=r.diff, fit_t=r.t))
for i, r in enumerate(tsel.head(3).itertuples(), 1):
    good, bad = (r.hi, r.lo) if r.t > 0 else (r.lo, r.hi)
    cfg["W"].append(dict(id=f"W{i}", fam=r.fam, trait=r.trait, up=good, down=bad, fit_diff=r.diff, fit_t=r.t, rho=r.rho))
json.dump(cfg, open(T + "configs.json", "w"), indent=1, default=float)
print(json.dumps({k: cfg[k] for k in ("X", "W")}, indent=1, default=float))
