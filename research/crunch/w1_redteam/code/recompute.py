"""W1-redteam recompute of headline figures from the live journals (run_id 1). Educational only - not financial advice.
Usage: python recompute.py <dir with primary.db ondeck.db testA..F.db gen.db graveyard.db>  (state branches mcf-data*).
R = pnl_adj / (|entry-stop| x shares); Rraw = pnl / risk (before costs); acctR = pnl_adj / (0.25% x equity).
Locked block 2024-11-01..2025-02-28 not read (live journals start 2026-10-06)."""
import sys, sqlite3, numpy as np, pandas as pd
D = sys.argv[1].rstrip('/') + '/'
ACC = ['primary','ondeck','testA','testB','testC','testD','testE','testF','gen','graveyard']
SIX = ['L3-gap-slope-fromopen-FD','RW3-gapdn-rsi5pop-flowsell-short-FD','RW5-heat30-flowsell-rsi5pop-gapdn-short-FD',
       'NS5-sma50-flush-oversold-long','ST7-rsi50dn-long-pm-t1s1-FD','NM-ETF-late-dip-di-long']
fr = []
for acc in ACC:
    df = pd.read_sql('select * from trades where run_id=1', sqlite3.connect(D + acc + '.db')); df['acct'] = acc; fr.append(df)
a = pd.concat(fr, ignore_index=True)
a['risk'] = (a.entry - a.stop).abs() * a.shares
a['R'] = a.pnl_adj / a.risk; a['Rraw'] = a.pnl / a.risk; a['cost'] = a.Rraw - a.R
a = a[np.isfinite(a.R)]
out = []
def put(k, v): out.append((k, v)); print(k, '=', v)
# 1 cost basis
for per, m in [('pre 11-12', a.date < '2026-11-12'), ('11-12+', a.date >= '2026-11-12')]:
    x = a[m]; put(f'cost/trade {per} mean|median|share no cost', f'{x.cost.mean():.3f}|{x.cost.median():.3f}|{((x.pnl_adj-x.pnl).abs()<1e-6).mean():.2f}')
# 2 Primary journal
p = a[(a.acct == 'primary') & (a.date <= '2026-11-17')]
g = p.groupby('date').R.sum(); gd = p.groupby('date').pnl_adj.sum()
put('Primary 10-06..11-17 sessions|R|green|median|$', f'{len(g)}|{g.sum():.1f}|{(g>0).sum()}|{g.median():.2f}|{gd.sum():.0f}')
x = g[g.index >= '2026-10-29']; put('Primary green since 10-29 (P3 says 43%)', f'{(x>0).sum()}/{len(x)}')
eq = np.where(p.date <= '2026-11-05', 95500, 83500)
put('Primary account R (pnl_adj / 0.25% equity; MTUM booking excluded)', f'{(p.pnl_adj/(0.0025*eq)).sum():.1f}')
# 3 six
s = p[p.strategy.isin(SIX)]; gs = s.groupby('date').R.sum()
put('six as traded in Primary trades|R|$|days|green', f'{len(s)}|{s.R.sum():.1f}|{s.pnl_adj.sum():.0f}|{len(gs)}|{(gs>0).sum()}')
post = a[(a.acct == 'primary') & (a.date >= '2026-11-11')].groupby('date').agg(R=('R','sum'), usd=('pnl_adj','sum'))
put('Primary post TEAM-6 (11-11..11-18) R by day', post.R.round(1).to_dict()); put('  $ by day', post.usd.round(0).to_dict())
pool = a[a.strategy.isin(SIX) & (a.date <= '2026-11-17')].groupby('date').R.sum()
put('six pooled all accounts (no latch replay) days|R|green%', f'{len(pool)}|{pool.sum():.1f}|{(pool>0).mean():.2f}')
# 4 NS5
n5 = a[(a.acct == 'primary') & (a.strategy == SIX[3])]
for hi in ['2026-11-17', '2026-11-18']:
    y = n5[n5.date <= hi]; gy = y.groupby('date').R.sum()
    put(f'NS5 Primary to {hi} n|R|Rraw|green days|w/o best|$', f'{len(y)}|{y.R.sum():.2f}|{y.Rraw.sum():.2f}|{(gy>0).sum()}/{len(gy)}|{y.R.sum()-gy.max():.2f}|{y.pnl_adj.sum():.0f}')
# 5 per setup R vs account R in Primary
pp = a[a.acct == 'primary'].copy(); pp['aR'] = pp.pnl_adj / (0.0025 * np.where(pp.date <= '2026-11-05', 95500, 83500))
t = pp.groupby('strategy').agg(n=('R','size'), R=('R','sum'), aR=('aR','sum'), med_risk=('risk','median')).sort_values('n', ascending=False).head(12)
print(t.round(2).to_string())
# 6 system R vs $ last 5 sessions
x = a[(a.date >= '2026-11-12') & (a.date <= '2026-11-18')]
put('system 11-12..11-18 R/session|$/session', f'{x.R.sum()/5:.1f}|{x.pnl_adj.sum()/5:.0f}')
pd.DataFrame(out, columns=['figure', 'value']).to_csv('recomputed.csv', index=False)
