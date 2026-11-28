"""Did the live record before a setup's first Primary session predict its Primary result? For every setup that traded
in Primary, its trades in other accounts BEFORE its first Primary date vs its Primary trades after (LR8 R, all of the
live record from 10-06). Read-only. Educational only - not financial advice."""
import sys
import numpy as np, pandas as pd
sys.path.insert(0, __file__.rsplit('/', 1)[0])
from load import load
t = load(sys.argv[1])
rows = []
for s, g in t.groupby('strategy'):
    p = g[g.account == 'primary']
    if not len(p): continue
    d0 = p.date.min(); pre = g[(g.account != 'primary') & (g.date < d0)]
    rows.append(dict(setup=s[:40], first_primary=d0, pre_n=len(pre), pre_avg=round(pre.r.mean(), 3) if len(pre) else np.nan,
                     prim_n=len(p), prim_avg=round(p.r.mean(), 3), prim_R=round(p.r.sum(), 1)))
r = pd.DataFrame(rows).sort_values('first_primary'); print(r.to_string(index=False))
q = r[r.pre_n >= 20]
print(f'setups with >= 20 pre-Primary live trades: {len(q)}; pre avg {q.pre_avg.mean():+.3f} -> Primary avg {q.prim_avg.mean():+.3f}; '
      f'spearman {q.pre_avg.corr(q.prim_avg, method="spearman"):+.2f}; pre>0 then Primary>0: {((q.pre_avg>0)&(q.prim_avg>0)).sum()} of {(q.pre_avg>0).sum()}')
