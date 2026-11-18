"""HKS950 15:30 slot re-cut (Lead lead-20261117-1900-3; Observer observer-20261117-1741-1). Descriptive, 0 new configs.
Same L20 ranks and days as hks950.py; the slot split from 1-min closes into
  A = 15:30 -> 15:55 (Live can reach: flat by 15:55),  B = 15:55 -> 16:00 (last 5 min; the auction print is not in 1-min bars)
plus a reproduction line (1-min 15:30 -> 16:00 vs the m30 slot).
  python3 -I recut.py <m30.csv.gz> <close_dir> <out.txt>          Educational only - not financial advice."""
import sys, glob, numpy as np, pandas as pd
sys.path.insert(0, '.')
from hks950 import prep, signal, tstat
x = prep(pd.read_csv(sys.argv[1])); z = signal(x, 20); z = z[z.hm == '1530']
c = pd.concat([pd.read_csv(f) for f in sorted(glob.glob(sys.argv[2] + '/*.csv.gz'))])
c['t'] = pd.to_datetime(c.t, utc=True).dt.tz_convert('America/New_York')
c['day'] = c.t.dt.date.astype(str); c['hm'] = c.t.dt.strftime('%H%M')
w = c.pivot_table(index=['symbol', 'day'], columns='hm', values='c', aggfunc='last')
def px(cols):  # last available close at or before the stated minute (within 3 min), else NaN
    return w[[k for k in cols if k in w]].ffill(axis=1).iloc[:, -1]
p30 = px(['1527', '1528', '1529']); p55 = px(['1552', '1553', '1554']); p60 = px(['1557', '1558', '1559'])
r = pd.DataFrame({'rA': p55 / p30 - 1, 'rB': p60 / p55 - 1, 'rAB': p60 / p30 - 1}).reset_index()
z = z.merge(r, on=['symbol', 'day'], how='left')
lines = [f"HKS950 15:30 re-cut: {len(z)} name-slots, {z.day.nunique()} days; 1-min coverage {z.rA.notna().mean():.3f}"]
def ls(col):
    g = z.dropna(subset=[col]).copy(); g['n'] = g.groupby('day').r.transform('size'); g['k'] = g.n // 10
    g['rk'] = g.groupby('day').sig.rank(method='first')
    top = g[g.rk > g.n - g.k].groupby('day')[col].mean(); bot = g[g.rk <= g.k].groupby('day')[col].mean(); mu = g.groupby('day')[col].mean()
    return pd.DataFrame({'ls': top - bot, 'lx': top - mu}).dropna() * 1e4
for col, lab in (('r', 'm30 slot 15:30-16:00 (as scored)'), ('rAB', '1-min 15:30-16:00 (reproduction)'), ('rA', 'A 15:30-15:55 (Live-reachable)'), ('rB', 'B 15:55-16:00 (last 5 min)')):
    d = ls(col)
    for nm, m in (('TRAIN', d.index < '2026-01-01'), ('VALID', d.index >= '2026-01-01')):
        dd = d[m]; lines.append(f"{lab} {nm}: days {len(dd)}  L-S {dd.ls.mean():+.2f} bps (t {tstat(dd.ls):+.2f})  long leg ex {dd.lx.mean():+.2f} (t {tstat(dd.lx):+.2f})")
lines.append("Reading: share of the slot reachable before 15:55 = A / (A+B) on VALID; cost 6 bps RT per leg still applies. Educational only - not financial advice.")
open(sys.argv[3], 'w').write('\n'.join(lines) + '\n'); print('\n'.join(lines))
