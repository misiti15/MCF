# Fetch GET-only Alpaca market data for the WB5 check: daily bars of traded symbols, 1-min SPY/QQQ, 1-min bars of
# CWT09-g10 and GEN-261027-08 trade symbol-days. Writes parquet under scratch wb5/. Educational only.
import sqlite3, glob, os, pandas as pd, numpy as np
from datetime import datetime, timedelta
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit
from alpaca.data.enums import Adjustment, DataFeed
S=__import__('os').environ.get('WB5_ROOT','.')
P={'CWT09':'CWT09-gapdn-vwaploss-g10-short','NS3':'NS3-failed-vwap-reclaim-short','MF2':'MF2-open-rsimidhi-flowsell-FD','MF4':'MF4-h40-open-flowsell-FD',
   'G2708':'GEN-261027-08-ORBfailDn-FromPCATRlem0p96-LUNCH-QQQltm0p6-hold-short','L3R':'L3-gap-slope-rsi5hi-FD'}
rows=[]
for f in glob.glob(S+'/j/*.db'):
    acct=os.path.basename(f)[:-3].replace('mcf-data-','').replace('mcf-data','primary')
    c=sqlite3.connect(f)
    q="select * from trades where run_id=1 and exit_time is not null and strategy in (%s)"%','.join('?'*len(P))
    d=pd.read_sql(q,c,params=list(P.values())); d['acct']=acct; rows.append(d)
t=pd.concat(rows,ignore_index=True)
t=t[(t.shares>0)&((t.entry-t.stop).abs()>0)]
cnt=t.groupby(['strategy','acct']).size().rename('nacct').reset_index(); t=t.merge(cnt,on=['strategy','acct'])
t=t.sort_values('nacct',ascending=False)
best=t.groupby(['strategy','symbol','date']).acct.first().rename('ka').reset_index()
t=t.merge(best,on=['strategy','symbol','date']); t=t[t.acct==t.ka].drop(columns=['ka'])
t['pnl_adj']=t.pnl_adj.fillna(t.pnl); t['R']=t.pnl_adj/((t.entry-t.stop).abs()*t.shares)
t.to_parquet(S+'/wb5/trades.parquet')
print(t.groupby('strategy').agg(n=('R','size'),days=('date','nunique'),R=('R','sum')))
cl=StockHistoricalDataClient(os.environ['ALPACA_API_KEY'],os.environ['ALPACA_SECRET_KEY'])
def bars(syms,start,end,tf):
    r=StockBarsRequest(symbol_or_symbols=syms,timeframe=tf,start=start,end=end,adjustment=Adjustment.SPLIT,feed=DataFeed.SIP)
    return cl.get_stock_bars(r).df
syms=sorted(t.symbol.unique())
dd=[]
for i in range(0,len(syms),100):
    dd.append(bars(syms[i:i+100],datetime(2026,9,25),datetime(2026,11,19),TimeFrame.Day))
pd.concat(dd).reset_index().to_parquet(S+'/wb5/daily.parquet')
m=bars(['SPY','QQQ'],datetime(2026,10,6,13),datetime(2026,11,18,21,30),TimeFrame(1,TimeFrameUnit.Minute))
m.reset_index().to_parquet(S+'/wb5/idx1m.parquet')
need=t[t.strategy.isin([P['CWT09'],P['G2708']])][['symbol','date']].drop_duplicates()
out=[]
for d,g in need.groupby('date'):
    day=pd.Timestamp(d)
    x=bars(sorted(g.symbol.unique()),day+timedelta(hours=13),day+timedelta(hours=21,minutes=30),TimeFrame(1,TimeFrameUnit.Minute))
    out.append(x.reset_index())
pd.concat(out).to_parquet(S+'/wb5/sym1m.parquet')
print('ok', len(need))
