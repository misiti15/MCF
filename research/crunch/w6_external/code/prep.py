"""Build the trade table with pre-open features. Educational only - not financial advice.
usage: prep.py <journal_dir> <daily.parquet> <out.pkl>"""
import sys, sqlite3, numpy as np, pandas as pd
J,D,O=sys.argv[1:4]
ACC=['primary','ondeck','testA','testB','testC','testD','testE','testF','gen','graveyard']
t=[]
for a in ACC:
    c=sqlite3.connect(f'{J}/{a}.db')
    x=pd.read_sql("select symbol,strategy,side,date,entry_time,entry,stop,shares,pnl_adj,exit_reason from trades where run_id=1 and pnl_adj is not null",c)
    x['acct']=a;t.append(x)
t=pd.concat(t,ignore_index=True)
t=t[(t.date>='2026-10-06')&(t.date<='2026-11-17')]
t['risk']=(t.entry-t.stop).abs()*t.shares
t=t[t.risk>0].copy();t['R']=t.pnl_adj/t.risk
t['et']=pd.to_datetime(t.entry_time,utc=True,format='mixed').dt.tz_convert('America/New_York')
t['hhmm']=t.et.dt.hour*100+t.et.dt.minute
d=pd.read_parquet(D);d['date']=d.ts.dt.tz_convert('America/New_York').dt.strftime('%Y-%m-%d')
d=d.sort_values(['symbol','date'])
g=d.groupby('symbol')
d['pc']=g.close.shift(1)
d['adv20']=(d.close*d.volume).groupby(d.symbol).transform(lambda s:s.shift(1).rolling(20,min_periods=10).mean())
d['ret5']=g.close.shift(1)/g.close.shift(6)-1
d['gap']=d.open/d.pc-1
t=t.merge(d[['symbol','date','pc','adv20','ret5','gap','open']],on=['symbol','date'],how='left')
spy=d[d.symbol=='SPY'][['date','close']].copy();spy['r']=np.log(spy.close).diff()
for L in (5,10,20): spy[f'rv{L}']=spy.r.shift(1).rolling(L).var()
t=t.merge(spy[['date','rv5','rv10','rv20']],on='date',how='left')
t['half']=np.where(t.date<='2026-10-27','fit','check')
t.to_pickle(O);print(t.shape, t.gap.notna().mean(), t.acct.value_counts().to_dict())
