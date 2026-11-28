"""Reviewer checks on track 7 (dev_tactics). Read-only on journal copies. Educational only - not financial advice.
1) promotion before/after vs the field over the same dates (regime control) and without MF4;
2) tau/reliability with leave-own-setup-out residual;
3) guards on what-if: skipped vs taken on the SAME day (paired daily diff), gross R."""
import sys, sqlite3
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'dev_tactics'))
from load import load
from mcf.research.shadow_calib import BRANCHES
D = sys.argv[1]
def dayt(x):
    x = np.asarray(x, float); x = x[~np.isnan(x)]
    return np.nan if len(x) < 3 or x.std(ddof=1) == 0 else x.mean() / (x.std(ddof=1) / np.sqrt(len(x)))
t = load(D)
# 1) promotion vs field
rows = []
for s, g in t.groupby('strategy'):
    p = g[g.account == 'primary']
    if not len(p): continue
    d0 = p.date.min(); pre = g[(g.account != 'primary') & (g.date < d0)]
    if len(pre) < 20: continue
    sd = np.sign(g.side.mean())
    fld = t[(np.sign(t.side) == sd) & (t.strategy != s)]
    f_pre = fld[fld.date.isin(pre.date.unique())]; f_post = fld[fld.date.isin(p.date.unique())]
    rows.append(dict(setup=s[:28], pre=pre.r.mean(), prim=p.r.mean(), field_pre=f_pre.r.mean(), field_prim=f_post.r.mean()))
r = pd.DataFrame(rows)
r['ex_pre'] = r.pre - r.field_pre; r['ex_prim'] = r.prim - r.field_prim
print(r.round(3).to_string(index=False))
print('mean pre %+.3f prim %+.3f | same-side field on same dates: pre %+.3f prim %+.3f | excess pre %+.3f -> prim %+.3f; excess>0 in Primary %d/10'
      % (r.pre.mean(), r.prim.mean(), r.field_pre.mean(), r.field_prim.mean(), r.ex_pre.mean(), r.ex_prim.mean(), (r.ex_prim > 0).sum()))
q = r[~r.setup.str.startswith('MF4')]
print('without MF4: prim %+.3f, excess prim %+.3f' % (q.prim.mean(), q.ex_prim.mean()))
# 2) leave-own-setup-out residual tau
w = t[t.date >= '2026-10-23'].copy(); w['sd'] = np.sign(w.side)
gs = w.groupby(['date', 'sd']).r.agg(['sum', 'count']); ss = w.groupby(['date', 'sd', 'strategy']).r.agg(['sum', 'count'])
m = ss.join(gs, rsuffix='_all'); m['loo'] = (m['sum_all'] - m['sum']) / (m['count_all'] - m['count']).replace(0, np.nan)
w = w.join(m['loo'], on=['date', 'sd', 'strategy']); w['res'] = w.r - w.loo
for minn in (30, 100):
    ys, vs = [], []
    for s, g in w.dropna(subset=['res']).groupby('strategy'):
        if len(g) < minn or g.date.nunique() < 8: continue
        ds = g.groupby('date').res.sum(); dn = g.groupby('date').size(); mm = ds.sum() / dn.sum()
        u = ds - mm * dn; k = len(dn); ys.append(mm); vs.append((u ** 2).sum() / dn.sum() ** 2 * k / (k - 1))
    y, v = np.array(ys), np.array(vs); wt = 1 / v; mu = (wt * y).sum() / wt.sum(); Q = (wt * (y - mu) ** 2).sum(); k = len(y)
    tau2 = max(0, (Q - (k - 1)) / (wt.sum() - (wt ** 2).sum() / wt.sum()))
    print(f'LOO residual n>={minn}: setups {k}, median SE {np.sqrt(np.median(v)):.3f}, tau {np.sqrt(tau2):.3f}, reliability {tau2/(tau2+np.median(v)):.2f}')
# 3) guards: same-day paired skipped minus taken (gross), since 11-12
parts = []
for acct, br in BRANCHES.items():
    con = sqlite3.connect(Path(D) / f'{br}.db')
    x = pd.read_sql("SELECT run_id, strategy, side, date, r_multiple, meta FROM trades WHERE run_id IN (1,2) AND exit_time IS NOT NULL AND date >= '2026-11-12'", con)
    con.close(); parts.append(x)
a = pd.concat(parts); a['date'] = a.date.astype(str).str[:10]
a['why'] = np.where(a.run_id == 1, 'LIVE', a.meta.fillna('').str.extract(r'why=([^;:(]+)')[0].fillna('?').str.strip())
a['why'] = a.why.str.replace(r'\d+(\.\d+)?', '#', regex=True).str[:40]
a['sd'] = np.sign(a.side)
live = a[a.run_id == 1].groupby(['date', 'sd']).r_multiple.mean()
for wy, g in a[a.run_id == 2].groupby('why'):
    if len(g) < 1000: continue
    gm = g.groupby(['date', 'sd']).r_multiple.agg(['mean', 'count'])
    j = gm.join(live.rename('live'), how='inner'); j['d'] = j['mean'] - j['live']
    dd = (j.d * j['count']).groupby(level=0).sum() / j['count'].groupby(level=0).sum()
    print(f'{wy[:34]:34s} n {len(g):5d} same-day-side skipped-minus-taken {np.average(j.d, weights=j["count"]):+.3f}  day t {dayt(dd.values):+.2f} days {len(dd)}')
