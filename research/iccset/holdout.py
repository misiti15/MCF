"""ICCSET-4 - time holdout for the group shrink target (Skeptic skeptic-20261112-0651-2). The five groups were drawn AFTER
seeing per-setup ICCs, so ICCSET-3's 40% is optimistic. This check uses new data for the test: ICC per setup on the first half
(10-20..10-31) and the second half (11-03..11-11) of the live window; does the first half's GROUP mean predict the second half's
setup ICC better than the first half's POOLED mean? Plus a bootstrap 90% CI per group (resampling setups, full window).
    python -I holdout.py <journal dir> <iccset_shrunk.csv>        Educational only - not financial advice."""
import sys, glob, os, sqlite3, re, numpy as np, pandas as pd
sys.argv_saved = sys.argv
exec(open("iccset.py").read().split("S = pd.read_csv")[0].replace("sys.argv[1]", "sys.argv_saved[1]"))   # loads T and icc1
Sh = pd.read_csv(sys.argv_saved[2])
fam = open("family.py").read(); ns = {"re": re, "np": np, "pd": pd}
exec(fam.split("D = pd.read_csv")[0].split('"""', 2)[2], ns); exec("def fam(s):" + fam.split("def fam(s):")[1].split("D[\"family\"]")[0], ns)
exec("def coarse(f):" + fam.split("def coarse(f):")[1].split("D[\"coarse\"]")[0], ns)
grp = {s: ns["coarse"](ns["fam"](s)) for s in Sh.setup}
rows = []
for s in Sh.setup:
    g = T[T.strategy == s]
    a, b = g[g.date <= "2026-10-31"], g[g.date >= "2026-11-03"]
    if a.date.nunique() >= 4 and b.date.nunique() >= 4 and len(a) >= 15 and len(b) >= 15:
        rows.append(dict(setup=s, group=grp[s], icc_a=icc1(a), icc_b=icc1(b), n_b=len(b)))
H = pd.DataFrame(rows).dropna()
pool_a = H.icc_a.mean(); gm_a = H.groupby("group").icc_a.mean()
H["pred_pool"] = pool_a; H["pred_grp"] = H.group.map(gm_a)
mse_p = ((H.icc_b - H.pred_pool) ** 2).mean(); mse_g = ((H.icc_b - H.pred_grp) ** 2).mean()
print(f"setups with >= 4 days and >= 15 trades in BOTH halves: {len(H)}")
print(f"first-half -> second-half: MSE pooled prior {mse_p:.4f}, group prior {mse_g:.4f} -> out-of-time variance explained {1 - mse_g / mse_p:+.0%}")
print(f"corr(icc_a, icc_b) per setup {H.icc_a.corr(H.icc_b):.2f}; group means first vs second half:")
print(pd.DataFrame({"n": H.groupby("group").size(), "first_half": gm_a, "second_half": H.groupby("group").icc_b.mean()}).round(3).to_string())
# bootstrap CI per group on the full-window raw ICC (resample setups within group)
rng = np.random.default_rng(7); Sh["group"] = Sh.setup.map(grp)
print("\nfull-window group ICC, bootstrap 90% CI over setups (2,000 draws; groups with < 5 setups are wide by construction):")
for gname, x in Sh.groupby("group"):
    v = x.icc.values; bs = [rng.choice(v, len(v)).mean() for _ in range(2000)]
    print(f"   {gname[:40]:40s} n {len(v):2d}  mean {v.mean():.3f}  90% CI [{np.percentile(bs, 5):.3f}, {np.percentile(bs, 95):.3f}]")
print("Educational only - not financial advice.")
