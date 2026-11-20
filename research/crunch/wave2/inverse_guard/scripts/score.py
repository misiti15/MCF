import sys,pandas as pd,numpy as np
WT='/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/rules1119'
W='/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/ig_tmp'
OUT=WT+'/research/crunch/wave2/inverse_guard'
sys.path.insert(0,WT+'/research/forward/compass_gate'); import shadow as S, inspect
src=inspect.getsource(S); lit=src.split('INVERSE = frozenset("""')[1].split('"""')[0].strip().split('\n')
IDX=set(lit[0].split()); INV=set(S.INVERSE); LV=set(S.LONG_VOL)
BROAD=set('SH SDS SPXU SPXS SPDN PSQ QID SQQQ DOG DXD SDOW RWM TWM TZA SRTY MZZ SMDD SBB'.split())
SETS={'G1':INV|LV,'G2':IDX|LV,'G3':BROAD|LV}
def awob(d):  # avg w/o best day, best-day share
    if len(d)==0: return np.nan,np.nan
    g=d.groupby('date').R.agg(['sum','count']); b=g['sum'].idxmax()
    n=len(d)-g.loc[b,'count']; tot=d.R.sum()
    return ((tot-g.loc[b,'sum'])/n if n else np.nan), (g.loc[b,'sum']/tot if tot>0 else np.nan)
def score(T,flag,key):
    out=[]
    for k,d in T.groupby(key):
        f=flag.loc[d.index]
        if not f.any(): continue
        k2=d[~f]; a0,s0=awob(d); a1,s1=awob(k2)
        out.append(dict(zip(key if isinstance(key,list) else [key], k if isinstance(k,tuple) else [k]),n=len(d),cut=int(f.sum()),cutR=d.R[f].sum(),
            base=d.R.sum(),new=k2.R.sum(),avg0=d.R.mean(),avg1=k2.R.mean() if len(k2) else np.nan,wob0=a0,wob1=a1,share0=s0,share1=s1))
    g=pd.DataFrame(out)
    if len(g): g['d']=g.new-g.base
    return g
def summ(g,lab):
    if not len(g): return f'| {lab} | 0 | | | | |'
    b=g[g.d>0.005]; w=g[g.d<-0.005]
    return f"| {lab} | {len(g)} ({int(g.cut.sum())} trades) | {len(b)} (+{b.d.sum():.1f}R) | {len(w)} ({w.d.sum():.1f}R) | {g.d.sum():+.1f}R | {w.d.min() if len(w) else 0:.1f}R |"
mode=sys.argv[1]
if mode=='live':
    T=pd.read_pickle(f'{W}/live.pkl').reset_index(drop=True); T['fam']=T.strategy.map(S.family_of)
    lines=[]; tabs={}
    for cfg in ['G1','G2','G3','M1','G1+M1']:
        st=SETS['G1']
        if cfg=='M1': fl=(T.side==1)&T.symbol.isin(st)
        elif cfg=='G1+M1': fl=T.symbol.isin(st)
        else: fl=(T.side==-1)&T.symbol.isin(SETS[cfg])
        for lab,X in [('all',T),('ex 11-19',T[T.date!='2026-11-19'])]:
            g=score(X,fl,['acct','strategy']); lines.append(summ(g,f'{cfg} {lab}'))
            if lab=='all':
                tabs[cfg]=g; gf=score(X,fl,'fam'); tabs[cfg+'_fam']=gf
                lines.append(summ(gf,f'{cfg} {lab} by family'))
                x=X[fl.loc[X.index]]; dd=x.groupby('date').R.sum()
                lines.append(f'|   removed: {len(x)} trades, {x.R.sum():+.1f}R, avg {x.R.mean():+.3f}, win {(x.R>0).mean():.0%}, days red {(dd<0).sum()}/{len(dd)}, avg w/o best day {awob(x)[0]:+.3f} | | | | | |')
    print('\n'.join(lines))
    for k,g in tabs.items():
        if len(g): g.round(3).to_csv(f'{OUT}/live_{k.replace("+","_")}.csv',index=False)
    # symbols
    x=T[(T.side==-1)&T.symbol.isin(SETS['G1'])]; print(x.groupby('symbol').R.agg(['count','sum']).round(1).sort_values('sum').T.to_string())
    x=T[(T.side==1)&T.symbol.isin(SETS['G1'])]; print('mirror syms',x.groupby('symbol').R.agg(['count','sum']).round(1).sort_values('sum').T.to_string())
    print('mirror by fam', x.groupby('fam').R.agg(['count','sum','mean']).round(2).sort_values('sum').to_string())
    # playing time
    g=tabs['G1']; g['frac']=g.cut/g.n; print('playing time >25%:'); print(g[(g.frac>0.25)][['acct','strategy','n','cut','base','new']].to_string())
    print('lowrep homes affected:'); print(g[g.acct.isin(['explore1','livelab'])][['acct','strategy','n','cut','base','new','d']].to_string())
