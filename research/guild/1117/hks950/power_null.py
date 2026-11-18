"""HKS950 power from the NULL only: random deciles, no signal. Educational only - not financial advice.
Usage: python3 -I power_null.py <scratch>/shortup_rth/m30.csv.gz"""
import sys, numpy as np, pandas as pd
d = pd.read_csv(sys.argv[1])
d['t'] = pd.to_datetime(d.t, utc=True).dt.tz_convert('America/New_York')
d['day'] = d.t.dt.date.astype(str); d['hm'] = d.t.dt.strftime('%H%M')
d = d[~d.day.isin(['2025-07-03', '2025-11-28', '2025-12-24'])]
d = d[(d.hm >= '0930') & (d.hm <= '1530')].sort_values(['symbol', 't'])
d['r'] = d.groupby(['symbol', 'day']).c.pct_change()
x = d[d.hm >= '1000'].dropna(subset=['r'])
rng = np.random.default_rng(1)
def rs(g):
    v = g.r.values; p = rng.permutation(len(v)); k = max(1, len(v) // 10)
    return v[p[:k]].mean() - v[p[-k:]].mean()
pd_ = x.groupby(['day', 'hm']).apply(rs).groupby(level=0).mean() * 1e4
for nm, sub in (('TRAIN', pd_[pd_.index < '2026-01-01']), ('VALID', pd_[pd_.index >= '2026-01-01'])):
    se = sub.std() / np.sqrt(len(sub))
    print(nm, len(sub), 'days; per-day sd %.2f bps; SE %.2f; MDE80 %.2f; at BAR90 1.35 -> %.2f bps' % (sub.std(), se, 2.8 * se, 2.19 * se))
print('Educational only - not financial advice.')
