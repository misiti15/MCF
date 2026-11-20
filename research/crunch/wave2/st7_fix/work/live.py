import glob, numpy as np, pandas as pd
W='/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/st7w'
LV='/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/rules1119/research/rootcause_1119/sl_work/live_all.pkl'
pd.set_option('display.width',250); pd.set_option('display.max_rows',300)
fz=pd.concat([pd.read_parquet(f) for f in glob.glob(W+'/scan/fires_*.parquet') if '_all' not in f])
F=pd.read_csv(W+'/family_delta.csv')
lv=pd.read_pickle(LV); lv['date']=lv.date.astype(str)
et=pd.to_datetime(lv.entry_time,utc=True).dt.tz_convert('America/New_York').dt.floor('5min')
lv['bar']=(et.dt.hour*100+et.dt.minute).astype(int)
def back(t,k):
    mins=(t//100)*60+t%100-5*k; return (mins//60)*100+mins%60
S={}
for v in ('base','SR','GA'):
    f=fz[fz['var']==v]; S[v]=set(zip(f.setup,f.symbol,f.date,f.tod))
cand=set(fz.setup)
L=lv[lv.strategy.isin(cand)].copy()
L['in_bars']=L.date<='2026-11-04'
def match(r,v):
    for k in (0,1,2):
        b=back(r.bar,k)
        if (r.strategy,r.symbol,r.date,b) in S[v]: return b
    return None
L['mb']=[match(r,'base') if r.in_bars else None for r in L.itertuples()]
for v in ('SR','GA'):
    L['keep_'+v]=[((r.strategy,r.symbol,r.date,int(r.mb)) in S[v]) if r.mb==r.mb and r.mb is not None else np.nan for r in L.itertuples()]
cov=L[L.in_bars]
print('live trades of scanned RSI-candidate setups:',len(L),'| with bars (<=11-04):',len(cov),'| matched to a base lab fire:',cov.mb.notna().sum(), f'({cov.mb.notna().mean():.0%})')
print('after 11-04 (no bars, not re-evaluable):',(~L.in_bars).sum(),'trades, R',round(L[~L.in_bars].R.sum(),1))
for v in ('SR','GA'):
    aff=set(F[F['var']==v].setup)
    m=cov[cov.mb.notna()&cov.strategy.isin(aff)]
    rem=m[m['keep_'+v]==False]
    g=m.groupby(['strategy','acct']).apply(lambda d:pd.Series({'n_matched':len(d),'R_matched':d.R.sum(),'n_removed':int((d['keep_'+v]==False).sum()),'R_removed':d.R[d['keep_'+v]==False].sum()}))
    g['delta']=-g.R_removed; gg=g[g.n_removed>0]
    print(f'\n== A-{v} live (removal only; trades the fix would add cannot be scored live): setup-accounts with removals {len(gg)}; better {(gg.delta>0).sum()} (+{gg.delta[gg.delta>0].sum():.1f}R) worse {(gg.delta<0).sum()} ({gg.delta[gg.delta<0].sum():.1f}R) net {gg.delta.sum():.1f}R; removed {len(rem)} of {len(m)} matched trades; removed avg R {rem.R.mean():.3f}')
    print(gg.sort_values('delta').round(2).to_string())
    print(' removed by bar:',rem.groupby('mb').R.agg(['size','sum']).round(2).to_dict('index'))
st=L[L.strategy.str.startswith('ST7-rsi50dn-long-pm-t1s1-FD')]
print('\nST7-FD family live:',st.groupby(['strategy','acct']).R.agg(['size','sum','mean']).round(3).to_string())
print('ST7-FD live matched:',st[st.in_bars].groupby('strategy').apply(lambda d:pd.Series({'n':len(d),'matched':d.mb.notna().sum(),'keep_SR':(d.keep_SR==True).sum(),'R_rem_SR':d.R[d.keep_SR==False].sum(),'keep_GA':(d.keep_GA==True).sum(),'R_rem_GA':d.R[d.keep_GA==False].sum()})).round(2).to_string())
# B / C on live ST7-FD (all live dates; rule by bar only)
for nm,keep in (('BWIN',lambda b:(b>=1335)&(b<=1500)),('CSKIP',lambda b:b!=1045)):
    for s,d in st.groupby('strategy'):
        b=d.bar.apply(lambda t:back(t,0)); k=keep(b)
        print(nm,s,'kept',int(k.sum()),'of',len(d),'R kept',round(d.R[k].sum(),2),'R removed',round(d.R[~k].sum(),2))
