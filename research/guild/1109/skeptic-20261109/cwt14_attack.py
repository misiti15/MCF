"""Skeptic attack on CWT14SKIP X1.5 from research/cwt14skip/cwt14_dist.csv.gz (Builder's per-trade file).
Same scoring as cwt14skip.py: excess = -(sum skipped R) minus the mean of 200 same-day, same-variant random blocks of equal
size; day-clustered t over all pool days. Extra cuts: plateau X grid (4 new X values = 4 counted looks -> lineage N 14),
symbol-day overlap of the skipped trades, half-year stability, one-symbol concentration.
usage: python cwt14_attack.py <cwt14_dist.csv.gz>      Educational only - not financial advice."""
import sys, numpy as np, pandas as pd
P = pd.read_csv(sys.argv[1]); P["date"] = pd.to_datetime(P.date).dt.date
r = P.r.to_numpy(); rng = np.random.default_rng(20261109)
grp = {k: g.index.to_numpy() for k, g in P.groupby(["date", "setup"])}
def score(skip, ndraw=200):
    ex = {}
    for (d, s), ii in grp.items():
        k = int(skip[ii].sum())
        if k == 0: ex[d] = ex.get(d, 0.0); continue
        real = -r[ii][skip[ii]].sum(); rnd = np.mean([-r[rng.choice(ii, k, replace=False)].sum() for _ in range(ndraw)])
        ex[d] = ex.get(d, 0.0) + real - rnd
    return pd.Series(ex).sort_index()
def t(s): return s.mean() / (s.std(ddof=1) / np.sqrt(len(s)))
print(f"pool {len(P)} trades, {P.date.nunique()} days")
print("\n(1) plateau (X in daily ATR below the open):")
E15 = None
for X in (1.0, 1.25, 1.5, 1.75, 2.0, 2.5):
    sk = (P.dist >= X).fillna(False).to_numpy(); E = score(sk)
    if X == 1.5: E15, SK15 = E, sk
    print(f"  X {X:4.2f}: skipped {sk.sum():6d}  skipped avg {r[sk].mean():+.3f}  excess {E.sum():+7.1f}  t {t(E):+.2f}")
S = P[SK15]
sd = S.groupby(["symbol", "date"]).size()
print(f"\n(2) overlap: {len(S)} skipped trades on {len(sd)} symbol-days (mean {sd.mean():.1f} trades each; "
      f"symbol-days with >= 4 variants firing: {(S.groupby(['symbol','date']).setup.nunique() >= 4).sum()})")
sdr = S.groupby(["symbol", "date"]).r.sum().sort_values()
print(f"    worst 5 skipped symbol-days (R removed = gain): {(-sdr.head(5)).round(1).to_dict()}")
print(f"    gain from the 10 worst symbol-days: {-sdr.head(10).sum():.1f} R of skipped total {-S.r.sum():.1f}")
sy = S.groupby("symbol").r.sum().sort_values(); print(f"    top 5 symbols by R removed: {(-sy.head(5)).round(1).to_dict()}")
h = pd.Series(pd.to_datetime(pd.Index(E15.index))).dt.to_period("Q").astype(str).to_numpy()
print("\n(3) X 1.5 excess by quarter:"); q = E15.groupby(h).agg(["sum", "count"])
q["t"] = E15.groupby(h).apply(t); print(q.round(2).to_string())
print(f"\n(4) size: pool {len(P)/P.date.nunique():.0f} trades/day; excess {E15.sum()/P.date.nunique():+.3f} R/day "
      f"= {E15.sum()/len(P):+.5f} R/trade")
print("Educational only - not financial advice.")
