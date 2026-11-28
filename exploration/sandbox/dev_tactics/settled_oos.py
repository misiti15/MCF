"""Out-of-sample version of the 'reps on settled setups' check. Settled = classified on the live record up to a cutoff
only (all accounts, LR8 R): >= 150 trades and avg R w/o best day <= -0.10, or day t <= -2 with >= 30 trades. Then the
following window: share of trades on those setups and their R/trade vs the rest. Read-only. Educational only."""
import sys
import numpy as np, pandas as pd
sys.path.insert(0, __file__.rsplit('/', 1)[0])
from load import load
t = load(sys.argv[1]); t = t[t.date >= '2026-10-23'].copy()
def dayt(x):
    x = np.asarray(x, float)
    return 0.0 if len(x) < 3 or x.std(ddof=1) == 0 else x.mean() / (x.std(ddof=1) / np.sqrt(len(x)))
def settled(h):
    out = set()
    for s, g in h.groupby('strategy'):
        ds = g.groupby('date').r.sum(); n = len(g)
        wo = (g.r.sum() - ds.max()) / max(n - (g.date == ds.idxmax()).sum(), 1)
        if (n >= 150 and wo <= -0.10) or (n >= 30 and dayt(g.groupby('date').r.mean()) <= -2): out.add(s)
    return out
for cut, end in (('2026-11-06', '2026-11-13'), ('2026-11-13', '2026-11-20'), ('2026-11-19', '2026-11-27')):
    S = settled(t[t.date <= cut]); f = t[(t.date > cut) & (t.date <= end)]
    a = f[f.strategy.isin(S)]; b = f[~f.strategy.isin(S)]
    da = a.groupby('date').r.mean(); db = b.groupby('date').r.mean(); d = (da - db).dropna()
    print(f'cut {cut} -> {end}: settled setups {len(S)}, their share of next-window trades {len(a)/len(f):.2f}, '
          f'R/trade settled {a.r.mean():+.3f} (n {len(a)}) vs rest {b.r.mean():+.3f} (n {len(b)}), '
          f'R settled {a.r.sum():+.0f} of {f.r.sum():+.0f}, daily diff t {dayt(d):+.2f}')
    gy = f[f.account == 'graveyard']
    print(f'   graveyard share of next-window trades {len(gy)/len(f):.2f}, its R/trade {gy.r.mean():+.3f}')
