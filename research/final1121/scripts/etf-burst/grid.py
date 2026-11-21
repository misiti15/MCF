"""ETF-BURST targeted rule grid (pre-declared 2026-11-21 before scoring; 15 configs).
Burst = >= K=4 raw signals of NM-ETF-late-dip-di-long in the same 5-min bar. Rule acts ONLY on burst bars and only when the
index condition says the burst bets AGAINST the index state (direction-adjusted: inverse ETFs count as short-index).
Conditions: C0 always (reference = plain burst cap, NOT proposed), C1 SPY below VWAP, C2 SPY/QQQ/IWM all below VWAP and below open
(Compass all-down analog), C3 SPY ret since 13:00 <= -0.25%, C4 SPY in bottom quarter of its day range.
Actions: A1 keep first lot per index group in the bar, A2 keep first 3 lots of the bar, A3 skip the burst.
Educational only - not financial advice."""
import sys, json
from base import *
K=4
def cond(x, c):
    d=np.where(x.inv,-1.0,1.0)
    if c=='C0': return np.ones(len(x),bool)
    if c=='C1': return d*x.spy_vw<0
    if c=='C2': return (d*x.spy_vw<0)&(d*x.qqq_vw<0)&(d*x.iwm_vw<0)&(d*x.spy_fo<0)&(d*x.qqq_fo<0)&(d*x.iwm_fo<0)
    if c=='C3': return d*x.spy_s1300<=-0.25
    if c=='C4': return np.where(x.inv, x.spy_pos>=0.75, x.spy_pos<=0.25)
    if c.startswith('V'):  # family B: index 15-min move vs SPY ATR14% (direction-adjusted) <= -X
        X={'V25':0.25,'V30':0.30,'V35':0.35}[c]; return d*x.spy_r15/x.atr14p <= -X
def apply(t, c, a):
    t=t.sort_values(['date','em','symbol'],kind='mergesort').reset_index(drop=True)
    nb=t.groupby(['date','tod']).symbol.transform('size').to_numpy()
    hit=(nb>=K)&np.asarray(cond(t,c),bool)
    keep=np.ones(len(t),bool)
    if a=='A1': rank=t.groupby(['date','tod','grp']).cumcount().to_numpy(); keep[hit&(rank>=1)]=False
    if a=='A2': rank=t.groupby(['date','tod']).cumcount().to_numpy(); keep[hit&(rank>=3)]=False
    if a=='A3': keep[hit]=False
    return t[keep], hit
def ctstat(x):
    return B.clustered_t(x) if len(x)>2 else np.nan
def summ(b, ns):
    if not len(b): return {}
    day=b.groupby('date').r.sum(); tot=b.r.sum(); s=day.sort_values(ascending=False)
    return dict(n=len(b), avg=b.r.mean(), tot=tot, R_per_ses=tot/ns, wo_best=b[b.date!=s.index[0]].r.mean(),
                wo_top2=b[~b.date.isin(s.index[:2])].r.mean(), best_share=s.iloc[0]/tot if tot>0 else np.nan,
                worst_day=day.min(), t=ctstat(b), green=(day>0).mean(), days=len(day))
def run(t, c, a, halves):
    tt,hit=apply(t,c,a)
    b=book(tt); b0=book(t)
    out={}
    for h in halves:
        x=b[b.half==h]; x0=b0[b0.half==h]
        d=x.groupby('date').r.sum(); d0=x0.groupby('date').r.sum()
        dd=d.reindex(d0.index.union(d.index),fill_value=0)-d0.reindex(d0.index.union(d.index),fill_value=0)
        ch=dd[dd.abs()>1e-9]
        out[h]=dict(**summ(x,NS[h]), dR=x.r.sum()-x0.r.sum(), days_better=int((ch>0).sum()), days_worse=int((ch<0).sum()),
                     better_sum=ch[ch>0].sum(), worse_sum=ch[ch<0].sum(), lots_cut=len(x0)-len(x),
                     d_t=(ch.mean()/(ch.std(ddof=1)/np.sqrt(len(ch))) if len(ch)>2 and ch.std()>0 else np.nan))
    return out
NS=sessions()
if __name__=='__main__':
    halves=sys.argv[1].split(',')
    t=load_raw().merge(pd.read_parquet('idx_feats.parquet'),on=['date','tod'],how='left').merge(pd.read_parquet('spy_daily.parquet'),left_on='date',right_index=True,how='left')
    t=t[t.half.isin(halves)]
    rows=[]
    b0=book(t)
    for h in halves: print('BASE',h,{k:round(v,3) for k,v in summ(b0[b0.half==h],NS[h]).items()})
    for c,a in [(c,a) for c in ['C0','C1','C2','C3','C4'] for a in ['A1','A2','A3']]+[(c,a) for c in ['V25','V30','V35'] for a in ['A1','A3']]:
        if True:
            o=run(t,c,a,halves)
            for h,v in o.items(): rows.append(dict(cfg=c+a,half=h,**v))
    R=pd.DataFrame(rows); pd.set_option('display.width',250)
    print(R[['cfg','half','n','avg','tot','dR','lots_cut','days_better','days_worse','better_sum','worse_sum','d_t','wo_best','wo_top2','worst_day','green','t']].round(3).to_string(index=False))
    R.to_csv(f'grid_{"_".join(halves)}.csv',index=False)
