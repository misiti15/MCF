"""How much real spread is there between setups? DerSimonian-Laird random-effects on each setup's live avg R
(10-23..11-27, all accounts, LR8, day-clustered standard error), raw and residual to the same-side day mean.
tau = SD of the TRUE per-setup avg R; reliability = share of observed spread that is real. Read-only."""
import sys
import numpy as np, pandas as pd
sys.path.insert(0, __file__.rsplit('/', 1)[0])
from load import load
t = load(sys.argv[1]); t = t[t.date >= '2026-10-23'].copy()
t['sd'] = np.sign(t.side); t['res'] = t.r - t.groupby(['date', 'sd']).r.transform('mean')
for col in ('r', 'res'):
  for minn in (30, 100):
    ys, vs, ns = [], [], []
    for s, g in t.groupby('strategy'):
        if len(g) < minn or g.date.nunique() < 8: continue
        dsum = g.groupby('date')[col].sum(); dn = g.groupby('date').size()
        m = dsum.sum() / dn.sum()
        # cluster-robust variance of the ratio mean
        u = dsum - m * dn; k = len(dn)
        v = (u ** 2).sum() / dn.sum() ** 2 * k / (k - 1)
        ys.append(m); vs.append(v); ns.append(len(g))
    y, v = np.array(ys), np.array(vs); w = 1 / v
    mu = (w * y).sum() / w.sum(); Q = (w * (y - mu) ** 2).sum(); k = len(y)
    tau2 = max(0, (Q - (k - 1)) / (w.sum() - (w ** 2).sum() / w.sum()))
    rel = tau2 / (tau2 + np.median(v))
    print(f'{col:3s} n>={minn}: setups {k}, observed SD of avg R {y.std(ddof=1):.3f}, median SE {np.sqrt(np.median(v)):.3f}, '
          f'tau (true SD) {np.sqrt(tau2):.3f}, reliability of a typical setup record {rel:.2f}, Q {Q:.0f} on {k-1} df')
