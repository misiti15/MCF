"""Where do the live reps go? Per account, 11-20..11-27 (FOOTRACE regime): sessions, trades/session, active setups, and
the share of trades spent on setups whose whole live record (10-23..11-27, all accounts) is already SETTLED
(>= 150 trades and avg R w/o best day <= -0.10, or day t <= -2), vs setups still under 30 trades. Read-only."""
import sys
import numpy as np, pandas as pd
sys.path.insert(0, __file__.rsplit('/', 1)[0])
from load import load
t = load(sys.argv[1]); t = t[t.date >= '2026-10-23'].copy()
def dayt(x):
    x = np.asarray(x, float)
    return 0.0 if len(x) < 3 or x.std(ddof=1) == 0 else x.mean() / (x.std(ddof=1) / np.sqrt(len(x)))
st = {}
for s, g in t.groupby('strategy'):
    ds = g.groupby('date').r.sum(); n = len(g)
    wo = (g.r.sum() - ds.max()) / max(n - (g.date == ds.idxmax()).sum(), 1)
    st[s] = dict(n=n, wo=wo, t=dayt(g.groupby('date').r.mean()))
st = pd.DataFrame(st).T
settled = set(st[((st.n >= 150) & (st.wo <= -0.10)) | ((st.t <= -2) & (st.n >= 30))].index)
young = set(st[st.n < 30].index)
w = t[t.date >= '2026-11-20']
rows = []
for a, g in w.groupby('account'):
    rows.append(dict(account=a, sessions=g.date.nunique(), trades=len(g), per_session=round(len(g) / g.date.nunique(), 1),
                     setups=g.strategy.nunique(), R=round(g.r.sum(), 1), R_per_trade=round(g.r.mean(), 3),
                     settled_share=round(g.strategy.isin(settled).mean(), 2), young_share=round(g.strategy.isin(young).mean(), 2)))
r = pd.DataFrame(rows); print(r.to_string(index=False))
print('settled setups', len(settled), '| settled share of all trades 11-20..11-27: %.2f' % w.strategy.isin(settled).mean(),
      '| R of settled trades %.1f of total %.1f' % (w[w.strategy.isin(settled)].r.sum(), w.r.sum()))
print('setups with < 30 trades:', len(young), '| setups total:', len(st))
