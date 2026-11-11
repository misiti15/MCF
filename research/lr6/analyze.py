# LR6 2026-11-11 (research only): cost tables, policy grid, adverse selection, train-picked rule sets scored once on valid.
# python analyze.py <out_dir>   (writes CSVs into out_dir; reads <S>/lr6/{trades_b,sim,trades}.pkl)
import sys, numpy as np, pandas as pd
S = '/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/lr6'
OUTD = sys.argv[1]
TRAIN_END = '2026-10-30'
MINFILL = 0.90
import os
OBJ = os.environ.get('LR6_OBJ', 'exec')   # 'delta' = pre-declared objective (net R per signal); 'exec' = without the book-skip effect
SUF = '' if OBJ == 'exec' else '_predeclared'
LBL = {'primary': 'Primary', 'testing': 'On Deck', 'testing2': 'Testing A', 'gen': 'Setup Generator',
       'graveyard': 'Graveyard', 'livelab': 'Testing C', 'explore1': 'Testing B'}

t = pd.read_pickle(f'{S}/trades_b.pkl')
sim = pd.read_pickle(f'{S}/sim.pkl')
POLS = list(dict.fromkeys(sim.index.get_level_values(0)))


def seg_cols(t):
    t['tod'] = pd.cut(t.ts.dt.hour * 60 + t.ts.dt.minute, [0, 600, 660, 780, 900, 2000],
                      labels=['09:30-10:00', '10:00-11:00', '11:00-13:00', '13:00-15:00', '15:00+'], right=False).astype(str)
    t['price_b'] = pd.cut(t.ref, [0, 20, 50, 100, 250, 1e9], labels=['<20', '20-50', '50-100', '100-250', '250+']).astype(str)
    t['adv_q'] = pd.qcut(t.adv, 4, labels=['Q1 low', 'Q2', 'Q3', 'Q4 high']).astype(str)
    t['atr_t'] = pd.qcut(t.atr_pct, 3, labels=['low', 'mid', 'high']).astype(str)
    t['spread_b'] = pd.cut(t.spread_bps, [-1, 5, 10, 20, 1e9], labels=['<5', '5-10', '10-20', '20+']).astype(str)
    t['mom_b'] = np.where(t.mom3_bps > 10, 'with (>+10)', np.where(t.mom3_bps < -10, 'against (<-10)', np.where(t.mom3_bps.notna(), 'flat', 'na')))
    c = t.compass.fillna('').str.lower()
    t['compass_b'] = np.where(c.str.contains('up'), 'up', np.where(c.str.contains('down'), 'down', np.where(c.str.contains('mixed'), 'mixed', 'na')))
    sm = t.groupby('strategy').mom3_bps.median()
    t['style'] = [('breakout/momentum' if sm.get(s, 0) > 0 else ('dip (long)' if sd > 0 else 'fade (short)')) for s, sd in zip(t.strategy, t.side)]
    t['side_s'] = np.where(t.side > 0, 'long', 'short')
    t['account'] = t.acct.map(LBL)
    t['qage_b'] = pd.cut(t.quote_age_s, [-1, 5, 15, 60, 300, 1e9], labels=['<=5', '5-15', '15-60', '60-300', '>300']).astype(str)
    t['split'] = np.where(t.date <= TRAIN_END, 'train', 'valid')
    return t


t = seg_cols(t)
SEGS = ['side_s', 'style', 'tod', 'price_b', 'adv_q', 'atr_t', 'spread_b', 'asset', 'spy_cond', 'compass_b', 'vol_regime', 'mom_b', 'account']

# ---------- Q1: today's entry cost (all trades incl. 11-11 partial) ----------
full = seg_cols(__import__('sim').base(pd.read_pickle(f'{S}/trades.pkl')))
full['slip_R'] = (full.side * (full.entry - full.ref)) / full.risk_plan
rows = []
for c in ['ALL'] + SEGS + ['family']:
    g = full.groupby(c if c != 'ALL' else np.zeros(len(full)))
    for k, x in g:
        rows.append(dict(dim=c, seg=k if c != 'ALL' else 'all', n=len(x), slip_bps_mean=x.slip_bps.mean(), slip_bps_med=x.slip_bps.median(),
                         slip_bps_p90=x.slip_bps.quantile(.9), half_spread_bps=x.spread_bps.mean() / 2, slip_R_mean=x.slip_R.mean(),
                         slip_R_med=x.slip_R.median(), share_neg_slip=(x.slip_bps <= 0).mean(), lat_s_med=x.lat_s.median()))
cost = pd.DataFrame(rows)
cost = cost[(cost.dim != 'family') | (cost.n >= 100)]
cost.round(4).to_csv(f'{OUTD}/entry_cost_by_segment.csv', index=False)

# ---------- policy evaluation helpers ----------
X = {}
for p in POLS:
    s = sim.loc[p]
    X[p] = s.reset_index(drop=True)
ok = X['O0_W15'].ok.values               # trades with bars (needed for the resting part)
T = t[ok].reset_index(drop=True)
for p in POLS:
    X[p] = X[p][ok].reset_index(drop=True)
Rm = T.R_mkt.values


def ev(p, mask=None, bound='p'):
    s = X[p]
    imm = s.imm.values.astype(float); pr = s[bound].values if p != 'M' else np.zeros(len(s))
    fill = imm + (1 - imm) * pr
    R = imm * Rm + (1 - imm) * pr * s.R_rest.values
    if p == 'M': fill, R = np.ones(len(s)), Rm.copy()
    if mask is not None: return fill[mask], R[mask]
    return fill, R


Rref = Rm + ((T.f_n - T.r_n) / T.risk_plan).values      # R had the trade filled at the signal price (gross of slip)


def exec_parts(p, mask):
    """per-trade split of the change vs market: price (better price on resting fills), selection (missed trades vs the
    sample's average market R), book (= what skipping the same share at random would give: -(miss) x average R)."""
    fill, R = ev(p, mask); rm = Rm[mask]; miss = 1 - fill; rbar = rm.mean()
    imm = X[p].imm.values[mask].astype(float) if p != 'M' else np.ones(mask.sum())
    price = (fill - imm) * (X[p].R_rest.values[mask] - rm) if p != 'M' else np.zeros(mask.sum())
    sel = -miss * (rm - rbar)
    book = -miss * rbar
    return price, sel, book


def summary(p, mask, days):
    fill, R = ev(p, mask)
    flo, _ = ev(p, mask, 'plo'); fhi, _ = ev(p, mask, 'phi')
    rm = Rm[mask]; d = R - rm; miss = 1 - fill
    dd = pd.DataFrame(dict(day=days[mask], d=d, R=R, n=1)).groupby('day').agg(d=('d', 'sum'), R=('R', 'sum'), n=('n', 'sum'))
    dm = dd.d / dd.n
    tstat = dm.mean() / dm.std(ddof=1) * np.sqrt(len(dm)) if len(dm) > 2 and dm.std(ddof=1) > 0 else np.nan
    best = dd.d.idxmax() if d.sum() > 0 else dd.d.idxmin()
    imm = X[p].imm.values[mask].astype(float) if p != 'M' else np.ones(mask.sum())
    rest_fill = fill - imm
    return dict(policy=p, n=int(mask.sum()), sessions=len(dd), fill=fill.mean(), fill_lo=flo.mean(), fill_hi=fhi.mean(),
                imm_fill=imm.mean(), reps_lost_per_session=miss.sum() / len(dd),
                R_sig=R.mean(), R_mkt=rm.mean(), dR_sig=d.mean(), t_day=tstat,
                dR_wo_best_day=(d.sum() - dd.d[best]) / (mask.sum() - dd.n[best]) if mask.sum() > dd.n[best] else np.nan,
                best_day_share=dd.d[best] / d.sum() if d.sum() != 0 else np.nan,
                R_mkt_of_missed=(miss * rm).sum() / miss.sum() if miss.sum() > 0 else np.nan,
                R_mkt_of_filled=(fill * rm).sum() / fill.sum(),
                saved_on_rest_fills=((rest_fill) * (X[p].R_rest.values[mask] - rm)).sum() / mask.sum() if p != 'M' else 0,
                lost_on_missed=-(miss * rm).sum() / mask.sum(),
                R_ref_of_missed=(miss * Rref[mask]).sum() / miss.sum() if miss.sum() > 0 else np.nan,
                R_ref_of_filled=(fill * Rref[mask]).sum() / fill.sum(),
                **xv(p, mask, days))


def xv(p, mask, days):
    price, sel, book = exec_parts(p, mask)
    ex = price + sel
    dd = pd.DataFrame(dict(day=days[mask], e=ex, n=1)).groupby('day').sum()
    dm = dd.e / dd.n
    tst = dm.mean() / dm.std(ddof=1) * np.sqrt(len(dm)) if len(dm) > 2 and dm.std(ddof=1) > 0 else np.nan
    best = dd.e.idxmax() if ex.sum() > 0 else dd.e.idxmin()
    return dict(d_price=price.mean(), d_selection=sel.mean(), d_book=book.mean(), exec_value=ex.mean(), exec_t_day=tst,
                exec_wo_best_day=(ex.sum() - dd.e[best]) / (mask.sum() - dd.n[best]) if mask.sum() > dd.n[best] else np.nan,
                exec_best_day_share=dd.e[best] / ex.sum() if ex.sum() else np.nan)


days = T.date.values
masks = {'all': np.ones(len(T), bool), 'train': (T.split == 'train').values, 'valid': (T.split == 'valid').values}
grid = []
for nm, m in masks.items():
    for p in POLS:
        r = summary(p, m, days); r['sample'] = nm; grid.append(r)
grid = pd.DataFrame(grid)
grid.round(4).to_csv(f'{OUTD}/policy_grid.csv', index=False)

# per-segment grid (all dates; description)
seg_rows = []
for c in SEGS + ['family']:
    for k in T[c].unique():
        m = (T[c] == k).values
        if m.sum() < 100: continue
        for p in POLS:
            r = summary(p, m, days); r.update(dim=c, seg=k); seg_rows.append(r)
seg = pd.DataFrame(seg_rows)
seg.round(4).to_csv(f'{OUTD}/policy_by_segment.csv', index=False)

# ---------- selection on train, one score on valid ----------
def pick(mask):
    best, bv = 'M', 0.0
    for p in POLS[1:]:
        fill, R = ev(p, mask)
        if fill.mean() < MINFILL: continue
        pr, se, bk = exec_parts(p, mask); v = (pr + se).mean() if OBJ == 'exec' else (R - Rm[mask]).mean()
        if v > bv: best, bv = p, v
    return best


tr = masks['train']; va = masks['valid']


def policy_mix(assign):   # assign: array of policy names per trade -> fill, R arrays
    fill = np.ones(len(T)); R = Rm.copy(); price = np.zeros(len(T))
    for p in set(assign):
        if p == 'M': continue
        m = assign == p
        f, r = ev(p, m); fill[m] = f; R[m] = r
        price[m] = (f - X[p].imm.values[m]) * (X[p].R_rest.values[m] - Rm[m])
    policy_mix.price = price
    return fill, R


def score(assign, mask, name):
    fill, R = policy_mix(assign)
    d = R - Rm
    ex = policy_mix.price - (1 - fill) * (Rm - Rm[mask].mean())
    dd = pd.DataFrame(dict(day=days[mask], d=d[mask], e=ex[mask], n=1, miss=1 - fill[mask])).groupby('day').sum()
    em = dd.e / dd.n; et = em.mean() / em.std(ddof=1) * np.sqrt(len(em)) if em.std(ddof=1) > 0 else np.nan
    be = dd.e.idxmax() if dd.e.sum() > 0 else dd.e.idxmin()
    dm = dd.d / dd.n
    tst = dm.mean() / dm.std(ddof=1) * np.sqrt(len(dm)) if dm.std(ddof=1) > 0 else np.nan
    best = dd.d.idxmax() if d[mask].sum() > 0 else dd.d.idxmin()
    # per family improve/worsen (owner remedy rule)
    fam = pd.DataFrame(dict(f=T.family[mask], d=ex[mask])).groupby('f').d.agg(['mean', 'size'])
    fam = fam[fam['size'] >= 20]
    out = dict(ruleset=name, n=int(mask.sum()), fill=fill[mask].mean(), reps_lost_per_session=dd.miss.sum() / len(dd),
               R_mkt=Rm[mask].mean(), R_sig=R[mask].mean(), dR_sig=d[mask].mean(), t_day=tst,
               dR_wo_best_day=(dd.d.sum() - dd.d[best]) / (dd.n.sum() - dd.n[best]), best_day_share=dd.d[best] / dd.d.sum() if dd.d.sum() else np.nan,
               exec_value=ex[mask].mean(), exec_t_day=et, exec_wo_best_day=(dd.e.sum() - dd.e[be]) / (dd.n.sum() - dd.n[be]),
               exec_best_day_share=dd.e[be] / dd.e.sum() if dd.e.sum() else np.nan, d_price=policy_mix.price[mask].mean(),
               fam_improve=int((fam['mean'] > 0.001).sum()), fam_worse=int((fam['mean'] < -0.001).sum()), fam_worst=fam['mean'].min())
    return out, fill, R


RS = {}
RS['market (today)'] = np.array(['M'] * len(T))
RS['LR6 as written'] = np.array(['P_LR6'] * len(T))
g = pick(tr); RS[f'(a) one global: {g}'] = np.array([g] * len(T))
choice_log = []
for nm, col in [('(b) by style', 'style'), ('(c) by momentum into signal', 'mom_b'), ('(d) by spread', 'spread_b'),
                ('(e) by price', 'price_b'), ('(f) by SPY condition', 'spy_cond')]:
    a = np.array(['M'] * len(T), dtype=object)
    for k in T[col].unique():
        m = (T[col] == k).values
        pk = pick(m & tr) if (m & tr).sum() >= 100 else 'M'
        a[m] = pk; choice_log.append(dict(ruleset=nm, seg=k, n_train=int((m & tr).sum()), policy=pk))
    RS[nm] = a
# (g) per setup with shrinkage toward family, family toward global
fam_d, set_d = {}, {}
for p in POLS[1:]:
    f, R = ev(p); pr, se, bk = exec_parts(p, np.ones(len(T), bool)); d = pr + se if OBJ == 'exec' else R - Rm
    df = pd.DataFrame(dict(s=T.strategy, fa=T.family, d=d, fill=f))[tr]
    G = df.d.mean(); Gf = df.fill.mean()
    fa = df.groupby('fa').agg(d=('d', 'mean'), fill=('fill', 'mean'), n=('d', 'size'))
    fa['d'] = (fa.n * fa.d + 100 * G) / (fa.n + 100); fa['fill'] = (fa.n * fa.fill + 100 * Gf) / (fa.n + 100)
    se = df.groupby(['s', 'fa']).agg(d=('d', 'mean'), fill=('fill', 'mean'), n=('d', 'size')).reset_index()
    se['d'] = (se.n * se.d + 50 * se.fa.map(fa.d)) / (se.n + 50); se['fill'] = (se.n * se.fill + 50 * se.fa.map(fa.fill)) / (se.n + 50)
    set_d[p] = se.set_index('s')
best_by_setup = {}
for s in T.strategy.unique():
    bp, bv = 'M', 0.0
    for p in POLS[1:]:
        if s not in set_d[p].index: continue
        r = set_d[p].loc[s]
        if r['fill'] >= MINFILL and r['d'] > bv: bp, bv = p, r['d']
    best_by_setup[s] = bp
RS['(g) per setup, shrunk'] = T.strategy.map(best_by_setup).values
pd.DataFrame(choice_log).to_csv(f'{OUTD}/ruleset_choices{SUF}.csv', index=False)
pd.Series(best_by_setup, name='policy').rename_axis('setup').to_csv(f'{OUTD}/setup_choice_train{SUF}.csv')

res = []; per_acct = []
for nm, a in RS.items():
    for spl, m in [('train', tr), ('valid', va)]:
        o, fill, R = score(a, m, nm); o['sample'] = spl; res.append(o)
    # per account on valid (expected change per signal and per session)
    fill, R = policy_mix(a)
    for ac in T.account.unique():
        m = va & (T.account == ac).values
        if m.sum() < 20: continue
        ns = len(set(days[m]))
        per_acct.append(dict(ruleset=nm, account=ac, n_valid=int(m.sum()), sessions=ns, trades_per_session_now=m.sum() / ns,
                             trades_per_session_policy=fill[m].sum() / ns, fill=fill[m].mean(), dR_sig=(R - Rm)[m].mean(),
                             dR_per_session=(R - Rm)[m].sum() / ns,
                             exec_value_sig=(policy_mix.price - (1 - fill) * (Rm - Rm[m].mean()))[m].mean(), R_mkt=Rm[m].mean()))
res = pd.DataFrame(res); res.round(4).to_csv(f'{OUTD}/rulesets_scored{SUF}.csv', index=False)
pd.DataFrame(per_acct).round(4).to_csv(f'{OUTD}/rulesets_by_account_valid{SUF}.csv', index=False)

# ---------- quote age (market entries) ----------
qa = []
q = full[full.quote_age_s.notna() & (full.date <= '2026-11-10')]
for A in [5, 15, 60, 300]:
    drop = q.quote_age_s > A
    for spl in ['train', 'valid', 'all']:
        m = np.ones(len(q), bool) if spl == 'all' else (q.split == spl).values
        x = q[m]; dx = drop[m]
        qa.append(dict(max_age_s=A, sample=spl, n=len(x), dropped=int(dx.sum()), drop_share=dx.mean(),
                       reps_lost_per_session=dx.sum() / x.date.nunique(), R_of_dropped=x.R_mkt[dx].mean(), R_of_kept=x.R_mkt[~dx].mean(),
                       slip_bps_dropped=x.slip_bps[dx].mean(), slip_bps_kept=x.slip_bps[~dx].mean(),
                       dR_sig=-(x.R_mkt[dx].sum()) / len(x)))
pd.DataFrame(qa).round(4).to_csv(f'{OUTD}/quote_age.csv', index=False)
qb = q.groupby('qage_b').agg(n=('R_mkt', 'size'), R=('R_mkt', 'mean'), slip_bps=('slip_bps', 'mean'), spread=('spread_bps', 'mean'))
qb.round(4).to_csv(f'{OUTD}/quote_age_buckets.csv')
T[['strategy', 'family', 'style']].drop_duplicates('strategy').to_csv(f'{OUTD}/setup_style.csv', index=False)
print('coverage', ok.mean(), len(T))
print(grid[grid['sample'] == 'all'][['policy', 'fill', 'fill_lo', 'fill_hi', 'reps_lost_per_session', 'dR_sig', 'd_price', 'd_selection', 'd_book', 'exec_value', 'exec_t_day', 'R_mkt_of_missed', 'R_ref_of_missed', 'R_ref_of_filled']].round(4).to_string())
print(res.round(4).to_string())
