"""Item 1(a) audit: enabled setups, universe reach, live trades in inverse / long-vol / leveraged products. Research only."""
import sys, glob, yaml, pandas as pd, numpy as np
WT='/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/rules1119'
W='/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/inv1120_tmp'
OUT=WT+'/research/owner1120/inverse'
sys.path.insert(0,WT+'/research/owner1120/inverse'); import shadow as S
ACC={'default':'primary','testing':'testing','testing2':'testing2','gen':'gen','graveyard':'graveyard','livelab':'livelab','explore1':'explore1','testingd':'testingd','testinge':'testinge','testingf':'testingf'}
en=[]
for f in sorted(glob.glob(WT+'/config/*.yaml')):
    k=f.split('/')[-1].replace('account_','').replace('.yaml','')
    if k not in ACC: continue
    y=yaml.safe_load(open(f)) or {}
    for n,s in (y.get('strategies') or {}).items():
        if not (isinstance(s,dict) and s.get('enabled')): continue
        syms=s.get('symbols') or s.get('pin_symbols') or s.get('trade_candidates')
        if isinstance(syms,list):
            cls=sorted({S.pclass(x) for x in syms}-{'stock_etf'}); reach='fixed list: '+(','.join(cls) if cls else 'no inv/lev')
        else: reach='scanner universe (incl. %d inverse/long-vol, lev funds)'%0
        en.append(dict(acct=ACC[k],strategy=n,type=s.get('type') or s.get('class'),reach=reach,sides=s.get('sides'),signal_symbol=s.get('signal_symbol')))
E=pd.DataFrame(en); E['fam']=E.strategy.map(S.family_of)
u=pd.read_csv(WT+'/data/universe.csv'); uc=u.symbol.map(S.pclass).value_counts(); print('universe.csv classes',uc.to_dict())
T=pd.read_pickle(f'{W}/live.pkl'); T['pc']=T.symbol.map(S.pclass); T['bs']=T.symbol.map(S.beta_sign)
T['exp']=T.side*T.bs; T['match']=np.where(T.bs==0,'neutral',np.where(T.exp==T.side,'yes','NO'))
sig=pd.read_pickle(f'{W}/sig.pkl'); sig['pc']=sig.symbol.map(S.pclass)
# setup side from live
sd=T.groupby('strategy').side.agg(lambda x:'both' if x.nunique()>1 else ('short' if x.iloc[0]<0 else 'long'))
SP=['inv_broad','inv_sector','inv_single','inv_crypto','long_vol','lev_long']
X=T[T.pc.isin(SP)]
a=X.groupby(['strategy','acct','side','pc']).agg(n=('R','size'),R=('R','sum'),avg=('R','mean'),win=('R',lambda r:(r>0).mean()),match=('match','first')).reset_index()
a['enabled_now']=[ ((E.strategy==s)&(E.acct==ac)).any() for s,ac in zip(a.strategy,a.acct)]
a.round(3).to_csv(OUT+'/audit_live_trades.csv',index=False)
# per enabled setup summary
sg=sig[sig.pc.isin(SP)].groupby(['acct','strategy']).size().rename('class_signals')
p=X.groupby(['acct','strategy']).agg(inv_n=('R',lambda r:0),).reset_index()
def agg(df,mask):
    d=df[mask]; return d.groupby(['acct','strategy']).R.agg(['count','sum'])
iv=agg(T,T.bs==-1).rename(columns={'count':'inv_n','sum':'inv_R'}); mm=agg(T,(T.bs==-1)&(T.side<0)).rename(columns={'count':'invshort_n','sum':'invshort_R'})
lv=agg(T,T.pc=='lev_long').rename(columns={'count':'lev_n','sum':'lev_R'}); al=T.groupby(['acct','strategy']).R.agg(['count','sum']).rename(columns={'count':'all_n','sum':'all_R'})
E2=E.set_index(['acct','strategy']).join([al,iv,mm,lv,sg]).fillna({'all_n':0,'inv_n':0,'invshort_n':0,'lev_n':0,'class_signals':0}).reset_index()
E2['side_live']=E2.strategy.map(sd)
E2.round(2).to_csv(OUT+'/audit_enabled.csv',index=False)
print('enabled setups',len(E2),'scanner reach',(E2.reach.str.startswith('scanner')).sum(),'fixed',(~E2.reach.str.startswith('scanner')).sum())
print(E2[~E2.reach.str.startswith('scanner')][['acct','strategy','reach','signal_symbol']].to_string())
print('enabled with any inv/vol live trade',(E2.inv_n>0).sum(),' with inv shorts',(E2.invshort_n>0).sum(),' with class signals',(E2.class_signals>0).sum())
# headline by class x side x match (all setups ever, run 1)
h=X.groupby(['pc','side']).agg(n=('R','size'),R=('R','sum'),avg=('R','mean'),setups=('strategy','nunique')).round(2); print(h.to_string())
print('thesis mismatch (inverse/vol) by side:',T[T.match=='NO'].groupby('side').R.agg(['count','sum','mean']).round(3).to_string())
# per setup list (all accounts, both sides) for inverse/vol
b=T[T.bs==-1].groupby(['strategy','side']).agg(accts=('acct',lambda x:','.join(sorted(set(x)))),n=('R','size'),R=('R','sum'),avg=('R','mean'),days=('date','nunique')).reset_index().sort_values('R')
b.round(3).to_csv(OUT+'/audit_inverse_by_setup.csv',index=False)
print('setups with inverse/vol trades',b.strategy.nunique(),'short-side',(b.side<0).sum(),'long-side',(b.side>0).sum())
print(b.head(15).round(2).to_string()); print(b.tail(10).round(2).to_string())
print('by family/side:'); T['fam']=T.strategy.map(S.family_of); print(T[T.bs==-1].groupby(['fam','side']).R.agg(['count','sum']).round(1).sort_values('sum').to_string())
