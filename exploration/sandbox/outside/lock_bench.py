"""Idea A on the bench: profit lock X = k * sd_day(FIT), CHECK and T2 scored separately.
Usage: python lock_bench.py <cand.parquet>. Educational only - not financial advice."""
import sys
import numpy as np
import pandas as pd
sys.path.insert(0, __file__.rsplit("/", 1)[0])
from common import tstat, summarize
from bench_book import load, book_day

c = load(sys.argv[1])
days = c.groupby("date").indices
per = c.groupby("date").per.first()
base_keep = np.zeros(len(c), bool)
for d, ix in days.items():
    base_keep[ix], _ = book_day(c.iloc[ix])
c["base"] = base_keep
bday = c[c.base].groupby("date").r.sum().reindex(per.index, fill_value=0.0)
for p in ["FIT", "CHECK", "T2"]:
    s = bday[per == p]
    print(f"BASE {p}: days {len(s)}, lots {int(c[c.base & (c.per == p)].shape[0])}, R/day {s.mean():+.2f}, sd {s.std():.2f}, red {int((s<=0).sum())}, worst5 {s.nsmallest(5).sum():+.1f}")
sd_fit = bday[per == "FIT"].std()
print(f"sd_day(FIT) = {sd_fit:.2f}R  (reference e4nb BASE: CHECK -3.03 R/day, T2 -1.80)")

# AM/PM descriptive on bench
rows = []
for d, ix in days.items():
    g = c.iloc[ix]; g = g[g.base]
    pm = g[g.em >= 720]
    if len(pm):
        rows.append((per[d], g.loc[g.xm <= 720, "r"].sum(), pm.r.sum(), len(pm)))
am = pd.DataFrame(rows, columns=["per", "am", "pm", "n"])
for p in ["CHECK", "T2"]:
    w = am[am.per == p]
    print(f"{p} AM/PM: corr(am, pm/n) spearman {w.am.corr(w.pm / w.n, method='spearman'):+.3f}; PM R/lot after AM green {w[w.am>0].pm.sum()/w[w.am>0].n.sum():+.3f} (n {w[w.am>0].n.sum()}), after AM red {w[w.am<=0].pm.sum()/w[w.am<=0].n.sum():+.3f} (n {w[w.am<=0].n.sum()})")

rng = np.random.default_rng(11)
out = []
for k in [0.25, 0.5, 1.0]:
    X = k * sd_fit
    keep = np.zeros(len(c), bool); lk = {}
    for d, ix in days.items():
        keep[ix], lk[d] = book_day(c.iloc[ix], X=X)
    nday = c[keep].groupby("date").r.sum().reindex(per.index, fill_value=0.0)
    for p in ["CHECK", "T2"]:
        m = per == p
        s = summarize(bday[m], nday[m])
        rem = c[c.base & ~keep & (c.per == p)]
        nrem = len(rem)
        pool = c[c.base & (c.per == p)].r.to_numpy()
        ctrl = np.array([-rng.choice(pool, nrem, replace=False).sum() for _ in range(1000)]) if nrem else np.zeros(1)
        dR = nday[m].sum() - bday[m].sum()
        # exposure-matched constant cut: scale every base lot by (1 - nrem/len(pool))
        f = 1 - nrem / len(pool); cc = bday[m] * f
        out.append(dict(k=k, X=round(X, 2), per=p, days=s["n_days"], locked_days=int(sum(lk[d] for d in per.index[m])),
                        lots_base=len(pool), lots_cut=nrem, dR_day=s["dR_day"], t=s["t"], removed_avgR=rem.r.mean() if nrem else np.nan,
                        base_avgR=pool.mean(), pct_vs_random=(ctrl < dR).mean() * 100,
                        red_base=s["red_base"], red_new=s["red_new"], red_constcut=int((cc <= 0).sum()),
                        w5_base=s["w5_base"], w5_new=s["w5_new"], w5_constcut=cc.nsmallest(5).sum(),
                        dR_wo_best=s["dR_wo_best"], best_share=s["best_share"]))
pd.set_option("display.width", 250)
print(pd.DataFrame(out).round(3).T.to_string())
