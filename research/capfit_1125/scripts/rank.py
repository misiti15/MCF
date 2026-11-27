import pandas as pd
t=pd.read_parquet('all_trades.parquet'); t=t[t.date<='2026-11-24']
rows=[]
for s,g in t.groupby('strategy'):
    dd=g.groupby('date').r.agg(['sum','size'])
    b=dd['sum'].idxmax()
    n=len(g); ns=len(dd)
    wo=(g.r.sum()-dd.loc[b,'sum'])/max(1,n-dd.loc[b,'size'])
    rows.append(dict(strategy=s,n=n,sess=ns,R=g.r.sum(),avg=g.r.mean(),avg_wo_best=wo,best_share=dd.loc[b,'sum']/g.r.sum() if g.r.sum()>0 else float('nan'),accts=','.join(sorted(g.account.unique()))))
r=pd.DataFrame(rows)
e=r[(r.n>=20)&(r.sess>=8)].sort_values('avg_wo_best',ascending=False)
pd.set_option('display.width',250); pd.set_option('display.max_colwidth',70)
print(len(r), len(e))
print(e.head(30).round(3).to_string(index=False))
P=['L3-gap-slope-fromopen-FD','NM-ETF-late-dip-di-long','RW3-gapdn-rsi5pop-flowsell-short-FD','RW5-heat30-flowsell-rsi5pop-gapdn-short-FD']
print(r[r.strategy.isin(P)].round(3).to_string(index=False))
sel=list(e.head(20).strategy)+[p for p in P if p not in list(e.head(20).strategy)]
pd.Series(sel).to_csv('setups.csv',index=False,header=False); print(len(sel))
