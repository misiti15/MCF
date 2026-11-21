"""CHECK 2025-10-01..2026-11-04 scored ONCE for the declared finalists V25A3, V30A3 (dev pass) and C1A1 (owner-spec reference).
Plus matched random-trim null (drop the same number of K>=4 burst bars at random). Educational only - not financial advice."""
from grid import *
t=load_raw().merge(pd.read_parquet('idx_feats.parquet'),on=['date','tod'],how='left').merge(pd.read_parquet('spy_daily.parquet'),left_on='date',right_index=True,how='left')
b0=book(t)
for h in ['fit','t2','check']: print('BASE',h,{k:round(float(v),3) for k,v in summ(b0[b0.half==h],NS[h]).items()})
rng=np.random.default_rng(7)
def null(tt, nbars, halves, draws=1000):
    x=tt[tt.half.isin(halves)].copy()
    nb=x.groupby(['date','tod']).symbol.transform('size'); bars=x.loc[nb>=K,['date','tod']].drop_duplicates().values.tolist()
    base=book(x).r.sum(); out=[]
    for _ in range(draws):
        pick=set(map(tuple,[bars[i] for i in rng.choice(len(bars),nbars,replace=False)]))
        m=~pd.Series(list(zip(x.date,x.tod)),index=x.index).isin(pick)
        out.append(book(x[m]).r.sum()-base)
    return np.array(out), len(bars)
for cfg in ['V25A3','V30A3','C1A1']:
    c,a=cfg[:-2],cfg[-2:]
    o=run(t,c,a,['fit','t2','check'])
    for h,v in o.items(): print(cfg,h,{k:(round(float(z),3) if z==z else None) for k,z in v.items()})
    if a=='A3':
        _,hit=apply(t,c,a); tt=t.sort_values(['date','em','symbol'],kind='mergesort').reset_index(drop=True)
        hb=tt[hit][['half','date','tod']].drop_duplicates()
        print(cfg,'burst bars cut:',hb.groupby('half').size().to_dict()); print(hb.to_string())
        for hs in (['fit','t2'],['check']):
            nbars=int(hb.half.isin(hs).sum())
            if nbars==0: print('null',hs,'no bars cut'); continue
            obs=sum(o[h]['dR'] for h in hs)
            dist,nb=null(t,nbars,hs,600)
            print('NULL',cfg,hs,'bars cut',nbars,'of',nb,'obs dR',round(obs,2),'null mean',round(dist.mean(),2),'p(null>=obs)',round((dist>=obs).mean(),3))
