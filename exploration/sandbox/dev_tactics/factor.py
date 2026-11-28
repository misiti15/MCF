"""How much of live setup R is one shared day/side factor? PCA of setup daily mean R (setups with >= 15 live days),
correlation with the same-side day mean, and the trade-R variance share explained by day x side. Read-only."""
import sys
import numpy as np, pandas as pd
sys.path.insert(0, __file__.rsplit('/', 1)[0])
from load import load
t = load(sys.argv[1]); t = t[t.date >= '2026-10-23'].copy()
dm = t.pivot_table(index='date', columns='strategy', values='r', aggfunc='mean')
ok = dm.columns[dm.notna().sum() >= 15]; X = dm[ok]
C = np.array(X.corr(min_periods=10).fillna(0).values, copy=True); np.fill_diagonal(C, 1)
ev = np.clip(np.linalg.eigvalsh(C), 0, None)[::-1]
print('setups', len(ok), 'PC1 share %.3f' % (ev[0] / ev.sum()), 'top3 %.3f' % (ev[:3].sum() / ev.sum()),
      'participation ratio (effective independent setups) %.1f' % (ev.sum() ** 2 / (ev ** 2).sum()), 'sessions', len(dm))
t['sd'] = np.sign(t.side); sm = t.groupby(['date', 'sd']).r.mean().unstack()
cs = []
for s in ok:
    side = np.sign(t[t.strategy == s].side.mean()); x = dm[s].dropna(); cs.append(x.corr(sm[side].loc[x.index]))
cs = np.array(cs)
print('median corr(setup day mean, same-side day mean) %.2f, share > 0.5: %.2f' % (np.nanmedian(cs), np.nanmean(cs > 0.5)))
res = t.r - t.groupby(['date', 'sd']).r.transform('mean')
print('trade-R variance explained by day x side: %.3f' % (1 - res.var() / t.r.var()))
# setup-day sums: variance explained by day x side
sdsum = t.groupby(['strategy', 'date', 'sd']).r.mean().reset_index()
r2 = sdsum.r - sdsum.groupby(['date', 'sd']).r.transform('mean')
print('setup-day mean variance explained by day x side: %.3f' % (1 - r2.var() / sdsum.r.var()))
