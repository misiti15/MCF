# LR6 2026-11-11 (research only): per-family / per-setup effect of the recommended rule "(d-wide)" (owner remedy rule),
# fill bounds, re-simulation count, and the 15 s quote-age cut per account.
import sys; sys.argv = [sys.argv[0], '.']
import numpy as np, pandas as pd
import analyze as A
T, Rm, days = A.T, A.Rm, A.days
ch = pd.read_csv('ruleset_choices.csv'); ch = ch[ch.ruleset == '(d) by spread'].set_index('seg').policy
wide = T.spread_b.isin(['10-20', '20+']).values
a = np.where(wide, A.RS['(d) by spread'], 'P_LR6')
fill, R = A.policy_mix(a); price = A.policy_mix.price
T = T.assign(fill=fill, dR=R - Rm, price=price, miss=1 - fill, Rm=Rm)
def tab(key):
    g = T.groupby(key)
    o = g.agg(n=('Rm', 'size'), sessions=('date', 'nunique'), R_mkt=('Rm', 'mean'), fill=('fill', 'mean'), dR_sig=('dR', 'mean'),
              d_price=('price', 'mean'), wide_share=('spread_b', lambda s: s.isin(['10-20', '20+']).mean()))
    o['exec_value'] = [(x.price - x.miss * (x.Rm - x.Rm.mean())).mean() for _, x in g]
    o['reps_lost_per_session'] = g.miss.sum() / o.sessions
    return o
fam = tab('family'); fam = fam[fam.n >= 20].sort_values('exec_value')
fam.round(4).to_csv('dwide_by_family.csv')
st = tab(['strategy', 'account']); st = st[st.n >= 20]
st.round(4).to_csv('dwide_by_setup_account.csv')
print(fam.round(4).to_string())
print('families improve/worse (exec):', (fam.exec_value > 0.001).sum(), (fam.exec_value < -0.001).sum(), ' dR:', (fam.dR_sig > 0.001).sum(), (fam.dR_sig < -0.001).sum())
prim = st.reset_index(); prim = prim[prim.account == 'Primary']
print(prim.round(4).to_string())
for p in ['O10_W300']:
    m = wide
    f, _ = A.ev(p, m); lo, _ = A.ev(p, m, 'plo'); hi, _ = A.ev(p, m, 'phi')
    print(p, 'wide fill point/lo/hi', f.mean().round(4), lo.mean().round(4), hi.mean().round(4), 'resim share of rest fills', A.X[p].resim.values[m].mean().round(4))
# 15 s quote age per account (market entries, trades with a logged quote age)
q = A.full[A.full.quote_age_s.notna() & (A.full.date <= '2026-11-10')]
r = []
for ac, x in q.groupby('account'):
    d = x.quote_age_s > 15; ns = x.date.nunique()
    r.append(dict(account=ac, n=len(x), dropped=int(d.sum()), drop_share=d.mean(), reps_lost_per_session=d.sum() / ns,
                  R_dropped=x.R_mkt[d].mean(), R_kept=x.R_mkt[~d].mean(), dR_sig=-x.R_mkt[d].sum() / len(x),
                  wide_share_of_dropped=x.spread_b[d].isin(['10-20', '20+']).mean()))
r = pd.DataFrame(r); r.round(4).to_csv('quote_age15_by_account.csv', index=False); print(r.round(4).to_string())
