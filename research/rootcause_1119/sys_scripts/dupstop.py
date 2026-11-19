import sqlite3,glob,os,pandas as pd,numpy as np
R='/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/rules1119/research/rootcause_1119'
rows=[]
for f in sorted(glob.glob(f'{R}/stk/*.db')):
    a=os.path.basename(f)[:-3]; c=sqlite3.connect(f)
    t=pd.read_sql("select strategy,symbol,side,date,entry_time,exit_time,entry,stop,shares,pnl_adj from trades where run_id=1 and pnl_adj is not null and shares>0 and entry!=stop",c)
    t['acct']=a; rows.append(t)
T=pd.concat(rows,ignore_index=True)
T=T[~T.date.between('2024-11-01','2025-02-28')]
T['et']=pd.to_datetime(T.entry_time.str.replace(' ','T'),format='ISO8601',utc=True); T['xt']=pd.to_datetime(T.exit_time.str.replace(' ','T'),format='ISO8601',utc=True)
T['rps']=(T.entry-T.stop).abs(); T['R']=T.pnl_adj/(T.rps*T.shares)
T=T.sort_values('et'); T['cls']='first'
for k,g in T.groupby(['acct','strategy','symbol','side','date']):
    idx=g.index.tolist()
    for j,i in enumerate(idx):
        prev=[p for p in idx[:j] if T.at[p,'xt']>T.at[i,'et']]
        if not idx[:j]: continue
        if not prev: T.at[i,'cls']='refire_flat'; continue
        d=min(abs(T.at[p,'stop']-T.at[i,'stop']) for p in prev)/T.at[i,'rps']
        T.at[i,'cls']='stack_samestop' if d<0.25 else 'stack_diffstop'
print(T.groupby('cls').R.agg(['count','sum','mean']).round(3))
for s in ['L3-gap-slope-fromopen-FD','ST7-rsi50dn-long-pm-t1s1-FD','RW3-gapdn-rsi5pop-flowsell-short-FD','RW5-heat30-flowsell-rsi5pop-gapdn-short-FD']:
    x=T[T.strategy==s]; print(s); print(x.groupby('cls').R.agg(['count','sum','mean']).round(3).T.to_string())
ex=T[T.date!='2026-11-19']; print('excl today'); print(ex.groupby('cls').R.agg(['count','sum','mean']).round(3))
g=T.groupby(['acct','strategy']).apply(lambda d: pd.Series(dict(n=(d.cls=='stack_samestop').sum(),dR=-d.R[d.cls=='stack_samestop'].sum())))
g=g[g.n>0]; print('remedy no same-stop stack: affected',len(g),'improve',(g.dR>0.005).sum(),round(g.dR[g.dR>0].sum(),1),'worse',(g.dR<-0.005).sum(),round(g.dR[g.dR<0].sum(),1),'net',round(g.dR.sum(),1))
print(g.sort_values('dR').head(8).round(2).to_string()); print(g.sort_values('dR').tail(5).round(2).to_string())
