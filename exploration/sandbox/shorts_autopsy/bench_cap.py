"""shorts_autopsy addendum A: family crowding cap C5/C10/C20 on the 6 gap-down short setups pooled (bench10 lots, LIVE-L),
vs 1,000 random removals of the same number of family lots and vs the exposure-matched constant cut. Reads bench_feat.parquet
from bench_score.py. Usage: python bench_cap.py WORK. Educational only - not financial advice."""
import sys
from pathlib import Path
import numpy as np, pandas as pd
W = Path(sys.argv[1]); x = pd.read_parquet(W / "bench_feat.parquet")
LOCK = ("2024-11-01", "2025-02-28"); assert not ((x.date >= LOCK[0]) & (x.date <= LOCK[1])).any()
NS = {"FIT": 170, "CHECK": 276, "T2": 427}
rng = np.random.default_rng(1128)
def capkeep(g, K):
    g = g.sort_values(["date", "em", "symbol"], kind="mergesort"); keep = np.zeros(len(g), bool)
    em, xm, dd = g.em.to_numpy(), g.xm.to_numpy(), g.date.to_numpy()
    start = 0
    for i in range(len(g)):
        if i == 0 or dd[i] != dd[i - 1]: openx = []
        openx = [e for e in openx if e > em[i]]
        if len(openx) < K: keep[i] = True; openx.append(xm[i])
    return pd.Series(keep, index=g.index)
rows = []
for per in ("CHECK", "T2", "FIT"):
    y = x[(x.per == per) & (x.fam == "gapdn")]
    if not len(y): continue
    days = NS[per]; daysum = y.groupby("date").r.sum()
    for K in (5, 10, 20):
        k = capkeep(y, K); rem = y[~k]
        gain = -rem.r.sum() / days
        dr = rem.groupby("date").r.sum().reindex(daysum.index, fill_value=0)
        v = np.r_[dr.to_numpy(), np.zeros(days - len(dr))]   # sessions without family lots count as 0
        t = -v.mean() / (v.std(ddof=1) / np.sqrt(days))
        r = y.r.to_numpy(); sims = np.array([-r[rng.choice(len(r), size=len(rem), replace=False)].sum() / days for _ in range(1000)])
        const = -(len(rem) / len(y)) * y.r.sum() / days
        after = y[k].groupby("date").r.sum().reindex(daysum.index, fill_value=0)
        ps = y.assign(rm=~k).groupby("setup").apply(lambda g: -g[g.rm].r.sum() / days)
        best = (-dr).max() / (-dr.sum()) if -dr.sum() > 0 else np.nan
        rows.append(dict(split=per, K=K, lots=len(y), removed=len(rem), share=len(rem) / len(y), dR_sess=gain, t=t,
                         pct_vs_random=(sims < gain).mean() * 100, const_cut=const, excess_vs_const=gain - const,
                         avgR_removed=rem.r.mean(), avgR_kept=y[k].r.mean(), worst5_before=daysum.nsmallest(5).sum(), worst5_after=after.nsmallest(5).sum(),
                         best_share=best, better=int((ps > 0).sum()), worse=int((ps < 0).sum())))
R = pd.DataFrame(rows); pd.set_option("display.width", 250); print(R.round(3).to_string())
R.to_csv(Path(__file__).with_name("bench_cap.csv"), index=False)
