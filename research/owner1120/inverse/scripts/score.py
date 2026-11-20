"""Item 1(b): H0 / H1 / H1M / H2 / H2D / H2S / H1-by-class / LEV-X, paired on each setup's own trades. Research only."""
import sys, re, pandas as pd, numpy as np
WT='/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/rules1119'
W='/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/inv1120_tmp'
OUT=WT+'/research/owner1120/inverse'
sys.path.insert(0,WT+'/research/owner1120/inverse'); import shadow as S
def prep(T):
    T=T.reset_index(drop=True).copy(); T['pc']=T.symbol.map(S.pclass); T['bs']=T.symbol.map(S.beta_sign); T['fam']=T.strategy.map(S.family_of); return T
live=prep(pd.read_pickle(f'{W}/live.pkl')); lab=prep(pd.read_pickle(f'{W}/lab.pkl'))
sig=pd.read_pickle(f'{W}/sig.pkl'); wi=pd.read_pickle(f'{W}/wi.pkl')
LIVEFIT='2026-11-05'; LABFIT='2025-11-01'
def awob(d):
    if len(d)==0: return np.nan,np.nan
    g=d.groupby('date').R.agg(['sum','count']); b=g['sum'].idxmax(); n=len(d)-g.loc[b,'count']; tot=d.R.sum()
    return ((tot-g.loc[b,'sum'])/n if n else np.nan),(g.loc[b,'sum']/tot if tot>0 else np.nan)
def score(T,rm,add,key):
    """paired: new = T[~rm] + add, grouped by key; only groups touched."""
    out=[]; A=add if add is not None and len(add) else T.iloc[:0]
    touched=set(map(tuple,T.loc[rm,key].drop_duplicates().values))|set(map(tuple,A[key].drop_duplicates().values))
    for k,d in T.groupby(key):
        k=k if isinstance(k,tuple) else (k,)
        if k not in touched: continue
        f=rm.loc[d.index]; a=A[(A[key]==pd.Series(k,index=key)).all(axis=1)] if len(A) else A
        new=pd.concat([d[~f],a]); a0,s0=awob(d); a1,s1=awob(new)
        out.append(dict(zip(key,k),n=len(d),cut=int(f.sum()),cutR=d.R[f].sum(),added=len(a),addR=a.R.sum() if len(a) else 0.0,
            base=d.R.sum(),new=new.R.sum(),avg0=d.R.mean(),avg1=new.R.mean() if len(new) else np.nan,wob0=a0,wob1=a1,share0=s0,share1=s1))
    g=pd.DataFrame(out)
    if len(g): g['d']=g.new-g.base
    return g
def summ(g,lab):
    if not len(g): return f'| {lab} | 0 | | | | |'
    b=g[g.d>0.005]; w=g[g.d<-0.005]
    return f"| {lab} | {len(g)} (-{int(g.cut.sum())} / +{int(g.added.sum())}) | {len(b)} (+{b.d.sum():.1f}R) | {len(w)} ({w.d.sum():.1f}R) | {g.d.sum():+.1f}R | {w.d.min() if len(w) else 0:.2f}R |"
INVV=lambda T:(T.bs==-1)
def cfg(T,name,src):
    """returns (remove mask, added rows) for config name on frame T (live or lab)."""
    rm=pd.Series(False,index=T.index); add=None
    if name=='H1': rm=INVV(T)&(T.side<0)
    elif name=='H1M': rm=INVV(T)
    elif name.startswith('H1-'):
        c={'broad':'inv_broad','sector':'inv_sector','single':'inv_single','crypto':'inv_crypto','vol':'long_vol'}[name[3:]]
        rm=(T.pc==c)&(T.side<0)
    elif name=='LEV-X': rm=T.pc=='lev_long'
    elif name in('H2','H2D'):
        rm=INVV(T)&(T.side<0); adds=[]
        if src=='live':   # inverse buy for skipped underlying shorts (borrow/spread/cost), R = run-2 what-if of the U short
            s=sig[(sig.side==-1)&sig.symbol.isin(S.INVERSE_OF)&(sig.status=='skipped')&sig.reason.fillna('').str.contains(S.INVBUY_REASONS)]
            s=s.drop_duplicates(['acct','strategy','symbol','day'])
            w=wi[wi.side==-1].drop_duplicates(['acct','strategy','symbol','date'])
            m=s.merge(w,left_on=['acct','strategy','symbol','day'],right_on=['acct','strategy','symbol','date'],how='left')
            print(f'  H2 inverse-buy opportunities (live): {len(m)} skipped underlying shorts, with what-if R {m.r_multiple.notna().sum()}')
            m=m[m.r_multiple.notna()]
            if len(m): adds.append(pd.DataFrame(dict(acct=m.acct,strategy=m.strategy,symbol=m.symbol.map(lambda u:S.INVERSE_OF[u][0]),side=1,date=m.day,R=m.r_multiple.astype(float)-0.02)))
        if name=='H2D':
            e=T[(T.side<0)&T.symbol.isin(S.INVERSE_OF)]
            adds.append(pd.DataFrame(dict(acct=e.acct,strategy=e.strategy,symbol=e.symbol.map(lambda u:S.INVERSE_OF[u][0]),side=1,date=e.date,R=e.R-0.02)))
        if adds:
            add=prep(pd.concat(adds,ignore_index=True))
    elif name=='H2S':
        cut=LIVEFIT if src=='live' else LABFIT
        fit=T[INVV(T)&((T.date<=cut) if src=='live' else (T.date<cut))]
        st=fit.groupby(['acct','strategy']).R.agg(['count','mean'])
        keep=set(st[(st['count']>=5)&(st['mean']>0)].index)
        print(f'  H2S {src}: setups kept on fit {len(keep)} of {len(st)} with fit inverse trades: {sorted(k[1] for k in keep)[:12]}')
        rm=INVV(T)&~pd.Series([ (a,s) in keep for a,s in zip(T.acct,T.strategy)],index=T.index)
        cfg.keep=keep
    return rm,add
CFGS=['H1','H1M','H2','H2D','H2S','H1-broad','H1-sector','H1-single','H1-crypto','H1-vol','LEV-X']
lines=['| config / window | affected (removed / added trades) | better | worse | net | largest worsening |','|---|---|---|---|---|---|']
fams=[]; per={}
for name in CFGS:
    for src,T in [('live',live),('lab',lab)]:
        rm,add=cfg(T,name,src)
        if src=='live':
            wins=[('all',T.date>=''),('ex 11-19',T.date!='2026-11-19'),('check 11-06..11-19',T.date>'2026-11-05')]
            key=['acct','strategy']
        else:
            wins=[('all',T.date>=''),('fit <2025-11',T.date<LABFIT),('check >=2025-11',T.date>=LABFIT)]
            key=['strategy']
        for wl,msk in wins:
            Y=T[msk]; A=add[add.date.isin(set(Y.date))] if add is not None else None
            g=score(Y,rm.loc[Y.index],A,key); lines.append(summ(g,f'{name} {src} {wl}'))
            if wl=='all':
                per[(name,src)]=g; gf=score(Y,rm.loc[Y.index],A,['fam']); lines.append(summ(gf,f'{name} {src} all, by family'))
                gf['cfg']=name; gf['src']=src; fams.append(gf)
                x=Y[rm.loc[Y.index]]
                if len(x): lines.append(f'|   removed {len(x)} trades {x.R.sum():+.1f}R avg {x.R.mean():+.3f} w/o best day {awob(x)[0]:+.3f}; added {0 if A is None else len(A)} {0 if A is None else A.R.sum():+.1f}R | | | | | |')
        if len(per[(name,src)]): per[(name,src)].round(3).to_csv(f'{OUT}/tables/{src}_{name}.csv',index=False)
pd.concat(fams).round(3).to_csv(f'{OUT}/tables/families.csv',index=False)
open(f'{OUT}/tables/headline.md','w').write('\n'.join(lines)+'\n')
print('\n'.join(lines))
# per-class blocked trades, live and lab, by side
for src,T in [('live',live),('lab',lab)]:
    x=T[T.pc.isin(['inv_broad','inv_sector','inv_single','inv_crypto','long_vol','lev_long'])]
    print(src,'class x side:'); print(x.groupby(['pc','side']).R.agg(['count','sum','mean']).round(3).to_string())
    if src=='lab':
        for h,m in [('fit',x.date<LABFIT),('check',x.date>=LABFIT)]: print(' ',h, x[m].groupby(['pc','side']).R.agg(['count','sum','mean']).round(3).to_string())
