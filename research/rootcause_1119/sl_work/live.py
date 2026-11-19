import sqlite3, pandas as pd, numpy as np, sys
sys.path.insert(0,'.')
from classify import classes
C,_=classes()
rows=[]
for db,acct in [('mcf-data.db','Primary'),('mcf-data-testing.db','Testing1')]:
    c=sqlite3.connect(db)
    t=pd.read_sql("select t.*, r.kind from trades t join runs r on r.id=t.run_id where strategy in ('L3-gap-slope-fromopen-FD','ST7-rsi50dn-long-pm-t1s1-FD')",c)
    t['acct']=acct; rows.append(t)
t=pd.concat(rows)
t['R']=t.pnl_adj/((t.entry-t.stop).abs()*t.shares)
t['cls']=t.symbol.map(lambda s:C.get(s,'?'))
t['et']=pd.to_datetime(t.entry_time,utc=True,format='mixed').dt.tz_convert('America/New_York')
t.to_pickle('live_trades.pkl')
def summ(g):
    d=g.groupby('date').R.sum()
    tot=g.R.sum(); best=d.max() if len(d) else np.nan
    return pd.Series({'n':len(g),'days':g.date.nunique(),'win':(g.R>0).mean(),'avgR':g.R.mean(),'totR':tot,
        'avgR_wo_best':(tot-best)/max(1,(len(g)-(g.date==d.idxmax()).sum())) if len(d) else np.nan,'best_share':best/tot if tot>0 else np.nan})
for kind in ['paper','whatif']:
  for st in ['L3-gap-slope-fromopen-FD','ST7-rsi50dn-long-pm-t1s1-FD']:
    x=t[(t.kind==kind)&(t.strategy==st)]
    print('\n',kind,st)
    print(x.groupby(['acct','cls']).apply(summ).round(3).to_string())
    print(x.groupby(['cls']).apply(summ).round(3).to_string())
