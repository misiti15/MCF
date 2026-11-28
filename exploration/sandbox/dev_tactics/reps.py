"""Rep economics per setup on the live record (all 10 accounts, LR8 R after costs, identical signals once).
Usage: python reps.py <dbdir>. Read-only. Educational only - not financial advice."""
import sys, json
import numpy as np, pandas as pd
sys.path.insert(0, __file__.rsplit('/', 1)[0])
from load import load

def dayt(x):
    x = np.asarray(x, float)
    if len(x) < 3 or x.std(ddof=1) == 0: return 0.0
    return x.mean() / (x.std(ddof=1) / np.sqrt(len(x)))

def main(dbdir):
    t = load(dbdir)
    t = t[t.date >= '2026-10-23']
    days = sorted(t.date.unique()); nd = len(days)
    out = {}
    rows = []
    for s, g in t.groupby('strategy'):
        dm = g.groupby('date').r.mean(); ds = g.groupby('date').r.sum()
        n = len(g); a = g.r.mean(); sd = g.r.std(ddof=1)
        best = ds.max(); wo = (g.r.sum() - best) / max(n - (g.date == ds.idxmax()).sum(), 1)
        acc = g.groupby('account').size().idxmax()
        rows.append(dict(setup=s, acct=acc, side='S' if g.side.mean() < 0 else 'L', n=n, days=len(dm), avg=a, sd=sd,
                         t=dayt(dm), wo=wo, best_share=(best / g.r.sum()) if g.r.sum() > 0 else np.nan,
                         tps=n / len(dm), gross=g.gross.mean()))
    r = pd.DataFrame(rows)
    r['cost'] = r.gross - r.avg
    # verdict classes
    r['cls'] = np.where(r.t <= -2, 'decisive-neg', np.where(r.t >= 2, 'decisive-pos', 'unresolved'))
    r.loc[(r.n < 30) | (r.days < 15), 'cls'] = 'too-few-reps'
    print(r.cls.value_counts().to_string())
    print('trades by class', r.groupby('cls').n.sum().to_dict())
    print('by account x class'); print(pd.crosstab(r.acct, r.cls).to_string())
    print('median per-trade SD', r.sd.median(), 'median trades/session', r.tps.median(), 'median cost R', r.cost.median())
    # sessions to detect effect d at day t 2 (approx: per-session mean SD = sd/sqrt(tps) ; needs (2*sigma_day/d)^2 days)
    sig_day = r.sd / np.sqrt(r.tps)
    for d in (0.05, 0.10, 0.20):
        need = (2 * sig_day / d) ** 2
        print(f'sessions to t=2 for +{d}R/trade: median {need.median():.0f}, p25 {need.quantile(.25):.0f}, p75 {need.quantile(.75):.0f}')
        need43 = (4.3 * sig_day / d) ** 2
        print(f'   at lineage bar t 4.3: median {need43.median():.0f}')
    r.to_csv(sys.argv[2] if len(sys.argv) > 2 else '/dev/null', index=False)
    # split-half persistence: setups with >= 60 trades, first half of their own dates vs second half
    ph = []
    for s, g in t.groupby('strategy'):
        ds = sorted(g.date.unique())
        if len(g) < 60 or len(ds) < 10: continue
        h = ds[len(ds) // 2]
        ph.append((s, g[g.date < h].r.mean(), g[g.date >= h].r.mean(), len(g)))
    ph = pd.DataFrame(ph, columns=['s', 'a1', 'a2', 'n'])
    print('split-half n', len(ph), 'spearman', ph.a1.corr(ph.a2, method='spearman').round(3),
          'pearson', ph.a1.corr(ph.a2).round(3))
    top = ph[ph.a1 >= ph.a1.quantile(.8)]; bot = ph[ph.a1 <= ph.a1.quantile(.2)]
    print('top quintile H1 avg', top.a1.mean().round(3), '-> H2', top.a2.mean().round(3), '| bottom', bot.a1.mean().round(3), '->', bot.a2.mean().round(3), '| all H2', ph.a2.mean().round(3))
    print('H1>0 share positive in H2', (ph[ph.a1 > 0].a2 > 0).mean().round(3), 'n', (ph.a1 > 0).sum(), '| H1<=0:', (ph[ph.a1 <= 0].a2 > 0).mean().round(3))
    # by trade-count bucket
    for lo, hi in ((60, 150), (150, 400), (400, 10**6)):
        q = ph[(ph.n >= lo) & (ph.n < hi)]
        if len(q) > 5: print(f' n {lo}-{hi}: k={len(q)} spearman {q.a1.corr(q.a2, method="spearman"):.3f}')
    return r

if __name__ == '__main__':
    main(sys.argv[1])
