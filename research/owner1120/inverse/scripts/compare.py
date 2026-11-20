"""Is the PRODUCT the problem? inverse/long-vol trades vs the same setups' stock trades (same side), live and lab halves."""
import sys, pandas as pd, numpy as np
WT='/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/rules1119'
W='/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/inv1120_tmp'
OUT=WT+'/research/owner1120/inverse'
sys.path.insert(0,OUT); import shadow as S
def prep(T):
    T=T.reset_index(drop=True).copy(); T['pc']=T.symbol.map(S.pclass); T['bs']=T.symbol.map(S.beta_sign); T['fam']=T.strategy.map(S.family_of); return T
live=prep(pd.read_pickle(f'{W}/live.pkl')); lab=prep(pd.read_pickle(f'{W}/lab.pkl'))
for src,T,wins in [('live',live,[('all',None),('to 11-05',T_:=None)]),('lab',lab,None)]:
    pass
def cmp(T,lab):
    out=[]
    for side in (-1,1):
        X=T[T.side==side]; st=set(X[X.bs==-1].strategy)
        X=X[X.strategy.isin(st)]
        inv=X[X.bs==-1]; stk=X[X.pc=='stock_etf']
        # paired by setup: mean of (inv avg - stock avg) weighted by inv n
        g=X.assign(k=np.where(X.bs==-1,'inv',np.where(X.pc=='stock_etf','stk','oth'))).groupby(['strategy','k']).R.mean().unstack()
        n=inv.groupby('strategy').size(); g=g.dropna(subset=['inv','stk']); w=n.reindex(g.index)
        diff=((g.inv-g.stk)*w).sum()/w.sum()
        out.append(f'| {lab} | {"short" if side<0 else "long"} | {len(st)} | {len(inv)} | {inv.R.mean():+.3f} | {stk.R.mean():+.3f} | {diff:+.3f} | {(g.inv<g.stk).sum()}/{len(g)} |')
    return out
lines=['| source | side | setups | inverse trades | inverse avg R | same setups stock/ETF avg R | paired gap (inv - stock, by setup) | setups where inverse worse |','|---|---|---|---|---|---|---|---|']
lines+=cmp(live,'live all'); lines+=cmp(live[live.date<='2026-11-05'],'live 10-06..11-05'); lines+=cmp(live[live.date>'2026-11-05'],'live 11-06..11-19')
lines+=cmp(lab[lab.date<'2025-11-01'],'lab fit half'); lines+=cmp(lab[lab.date>='2025-11-01'],'lab check half')
# by class
for c in ['inv_broad','inv_sector','inv_single','long_vol']:
    for src,T in [('live',live),('lab',lab)]:
        Y=T[(T.bs!=-1)|(T.pc==c)]; lines+=[l.replace('| '+src,'| '+src+' '+c,1) for l in cmp(Y,src)]
open(OUT+'/tables/inverse_vs_stock.md','w').write('\n'.join(lines)+'\n'); print('\n'.join(lines))
