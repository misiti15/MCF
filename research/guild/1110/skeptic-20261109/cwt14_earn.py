"""Skeptic: share of CWT14SKIP X1.5 skips inside the live earnings blackout (+-4 busdays, as mcf.research.generator.data._blackout,
open-block earnings file from research-data), and the excess with blackout trades removed from the pool (live never trades them).
usage: python cwt14_earn.py <cwt14_dist.csv.gz> <earnings_yf.parquet>   Educational only - not financial advice."""
import sys, numpy as np, pandas as pd
P = pd.read_csv(sys.argv[1]); er = pd.read_parquet(sys.argv[2], columns=["symbol", "date"]).dropna()
d = np.array(pd.to_datetime(er.date).dt.date.astype(str), dtype="datetime64[D]")
bl = set()
for k in range(-4, 5):
    for s, x in zip(er.symbol.astype(str), np.busday_offset(d, k, roll="forward").astype(str)): bl.add(s + "|" + x)
P["bl"] = (P.symbol.astype(str) + "|" + P.date.astype(str)).isin(bl)
P["date"] = pd.to_datetime(P.date).dt.date; sk = (P.dist >= 1.5).fillna(False)
print(f"pool blackout share {P.bl.mean():.1%}; X1.5 skipped {sk.sum()}, of which in blackout {P.bl[sk].mean():.1%}")
print(f"skipped avg R: in blackout {P.r[sk & P.bl].mean():+.3f} (n {int((sk & P.bl).sum())}); outside {P.r[sk & ~P.bl].mean():+.3f} (n {int((sk & ~P.bl).sum())})")
Q = P[~P.bl].reset_index(drop=True); r = Q.r.to_numpy(); s2 = (Q.dist >= 1.5).fillna(False).to_numpy(); rng = np.random.default_rng(20261109)
ex = {}
for (dd, st), g in Q.groupby(["date", "setup"]):
    ii = g.index.to_numpy(); k = int(s2[ii].sum())
    if k == 0: ex[dd] = ex.get(dd, 0.0); continue
    ex[dd] = ex.get(dd, 0.0) - r[ii][s2[ii]].sum() - np.mean([-r[rng.choice(ii, k, replace=False)].sum() for _ in range(200)])
E = pd.Series(ex); print(f"blackout-free pool (as live): skipped {s2.sum()}, excess {E.sum():+.1f}R, t {E.mean() / (E.std(ddof=1) / np.sqrt(len(E))):.2f}")
print("Educational only - not financial advice.")
