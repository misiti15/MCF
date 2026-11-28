"""Idea A robustness (no new config): k=0.25 profit lock on the bench, by half-period (CHECK H1/H2, T2 H1/H2):
red days, dR/day, removed-lot avg R vs base avg. Usage: python lock_halves.py <cand.parquet>. Educational only - not financial advice."""
import sys
import numpy as np
import pandas as pd
sys.path.insert(0, __file__.rsplit("/", 1)[0])
from common import tstat
from bench_book import load, book_day

c = load(sys.argv[1]); days = c.groupby("date").indices; per = c.groupby("date").per.first()
bk = np.zeros(len(c), bool); lk = np.zeros(len(c), bool)
for d, ix in days.items():
    bk[ix], _ = book_day(c.iloc[ix])
bday = c[bk].groupby("date").r.sum().reindex(per.index, fill_value=0.0)
X = 0.25 * bday[per == "FIT"].std()
for d, ix in days.items():
    lk[ix], _ = book_day(c.iloc[ix], X=X)
nday = c[lk].groupby("date").r.sum().reindex(per.index, fill_value=0.0)
for p in ["CHECK", "T2"]:
    ds = per.index[per == p]; h = len(ds) // 2
    for lab, dd in [("H1", ds[:h]), ("H2", ds[h:])]:
        rem = c[bk & ~lk & c.date.isin(dd)]; base = c[bk & c.date.isin(dd)]
        diff = nday[dd] - bday[dd]
        print(f"{p} {lab} ({dd[0]}..{dd[-1]}): days {len(dd)}, red {int((bday[dd]<=0).sum())} -> {int((nday[dd]<=0).sum())}, "
              f"dR/day {diff.mean():+.2f} (t {tstat(diff):+.2f}), removed avg R {rem.r.mean():+.3f} vs base {base.r.mean():+.3f}, lots cut {len(rem)/len(base):.1%}")
