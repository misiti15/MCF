"""Does a setup's live record predict its own next stretch? Split each setup's live sessions (10-23..11-27, LR8 R,
all accounts, identical signals once) into first/second half; also a residual version (R minus the same-side, same-day
mean over all setups) to strip the day/side regime. Control: 1000 label shuffles. Read-only. Educational only."""
import sys
import numpy as np, pandas as pd
sys.path.insert(0, __file__.rsplit('/', 1)[0])
from load import load

t = load(sys.argv[1]); t = t[t.date >= '2026-10-23'].copy()
t['sd'] = np.sign(t.side)
t['res'] = t.r - t.groupby(['date', 'sd']).r.transform('mean')
rng = np.random.default_rng(7)
def split(col, minn):
    out = []
    for s, g in t.groupby('strategy'):
        ds = sorted(g.date.unique())
        if len(g) < minn or len(ds) < 10: continue
        h = ds[len(ds) // 2]
        out.append((g[g.date < h][col].mean(), g[g.date >= h][col].mean(), len(g)))
    return pd.DataFrame(out, columns=['a1', 'a2', 'n'])
for col in ('r', 'res'):
    for minn in (30, 60, 150):
        p = split(col, minn)
        rho = p.a1.corr(p.a2, method='spearman')
        null = [p.a1.corr(pd.Series(rng.permutation(p.a2.values)), method='spearman') for _ in range(1000)]
        top = p[p.a1 >= p.a1.quantile(.75)]
        print(f'{col:3s} n>={minn:3d} k={len(p):3d} spearman {rho:+.3f} (null 95% band {np.quantile(null,.025):+.3f}..{np.quantile(null,.975):+.3f}) '
              f'top-quartile H1 {top.a1.mean():+.3f} -> H2 {top.a2.mean():+.3f} vs all H2 {p.a2.mean():+.3f}')
# weekly rank persistence (week w top-10 by total R -> week w+1 avg R) like the promotion standard
t['wk'] = pd.to_datetime(t.date).dt.to_period('W').astype(str)
wk = sorted(t.wk.unique()); res = []
for a, b in zip(wk[:-1], wk[1:]):
    A = t[t.wk == a].groupby('strategy').r.agg(['sum', 'count']); A = A[A['count'] >= 10]
    B = t[t.wk == b].groupby('strategy').r.mean()
    top = A.sort_values('sum').index[-10:]; c = [x for x in top if x in B.index]
    allb = B[B.index.isin(A.index)]
    res.append((a, len(c), B[c].mean(), allb.mean()))
print(pd.DataFrame(res, columns=['week', 'top10_next', 'top10_next_avgR', 'all_next_avgR']).round(3).to_string(index=False))
