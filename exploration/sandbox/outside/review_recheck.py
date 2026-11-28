"""Reviewer re-check for track 6 (no new configs counted as candidates; 1 control family).
Reproduces bench base + k=0.25 profit-lock red days, then adds two path controls:
 (a) day-level transitions (red->green saved vs green->red created),
 (b) a lot-count-matched "first-N lots per day" cap (same total lots removed per period, N found by search) -
     tests whether ANY early stop also cuts red days, i.e. whether the lock's trigger (closed R >= X) matters.
Usage: python review_recheck.py <cand.parquet>. Educational only - not financial advice."""
import sys
import numpy as np
import pandas as pd
sys.path.insert(0, __file__.rsplit("/", 1)[0])
from bench_book import load, book_day

c = load(sys.argv[1]); days = c.groupby("date").indices; per = c.groupby("date").per.first()
bk = np.zeros(len(c), bool)
for d, ix in days.items():
    bk[ix], _ = book_day(c.iloc[ix])
bday = c[bk].groupby("date").r.sum().reindex(per.index, fill_value=0.0)
X = 0.25 * bday[per == "FIT"].std()
lk = np.zeros(len(c), bool)
for d, ix in days.items():
    lk[ix], _ = book_day(c.iloc[ix], X=X)
nday = c[lk].groupby("date").r.sum().reindex(per.index, fill_value=0.0)
print(f"X = {X:.2f}R")
c["base"] = bk; c["rank"] = c[bk].groupby("date").cumcount().reindex(c.index)
for p in ["CHECK", "T2"]:
    ds = per.index[per == p]; b, n = bday[ds], nday[ds]
    rem = int((bk & ~lk & (c.per == p).to_numpy()).sum())
    print(f"{p}: R/day base {b.mean():+.2f}, red {int((b<=0).sum())} -> {int((n<=0).sum())}; saved red->green {int(((b<=0)&(n>0)).sum())}, "
          f"created green->red {int(((b>0)&(n<=0)).sum())}; green-day avg R base {b[b>0].mean():+.2f} lock {n[n>0].mean():+.2f}; lots removed {rem}")
    # first-N cap matched on total lots removed
    sub = c[bk & (c.per == p).to_numpy()]
    best = None
    for N in range(1, 200):
        cut = int((sub["rank"] >= N).sum())
        if best is None or abs(cut - rem) < abs(best[1] - rem):
            best = (N, cut)
    N, cut = best
    cd = sub[sub["rank"] < N].groupby("date").r.sum().reindex(ds, fill_value=0.0)
    print(f"   first-N cap N={N} (lots removed {cut}): red {int((cd<=0).sum())}, dR/day {(cd-b).mean():+.2f}, lock dR/day {(n-b).mean():+.2f}")
