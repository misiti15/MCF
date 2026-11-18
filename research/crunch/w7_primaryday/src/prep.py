import sqlite3,pandas as pd,numpy as np,json
c=sqlite3.connect('p.db')
t=pd.read_sql("select id,symbol,strategy,side,date,signal_time,entry_time,exit_time,entry,stop,exit,exit_reason,shares,pnl_adj,mae_r,mfe_r from trades where run_id=1 and date>='2026-10-06'",c)
t['R']=t.pnl_adj/((t.entry-t.stop).abs()*t.shares)
for k in ['signal_time','entry_time','exit_time']:
    t[k]=pd.to_datetime(t[k],utc=True,format='mixed').dt.tz_convert('America/New_York')
t['bar']=t.signal_time.dt.floor('5min')
t['hm']=t.entry_time.dt.hour*60+t.entry_time.dt.minute
t=t.sort_values(['entry_time','id']).reset_index(drop=True)
# index 5-min
m=pd.read_parquet('mkt/idx5.parquet'); m['t']=pd.to_datetime(m.t,utc=True).dt.tz_convert('America/New_York')
m=m[(m.t.dt.hour*60+m.t.dt.minute>=570)&(m.t.dt.hour*60+m.t.dt.minute<960)]
m['d']=m.t.dt.strftime('%Y-%m-%d')
spy=m[m.S=='SPY'].copy()
op=spy.groupby('d').o.first(); cl=spy.groupby('d').c.last()
dl=pd.read_parquet('mkt/daily.parquet'); dl['d']=pd.to_datetime(dl.t).dt.strftime('%Y-%m-%d')
sd=dl[dl.S=='SPY'].set_index('d').c; prevc=sd.shift(1)
day=pd.DataFrame({'spy_oc':(cl/op-1)*100,'spy_gap':(op/prevc.reindex(op.index)-1)*100})
# SPY price at time (last close of 5-min bar ending <= ts)
spy['tend']=spy.t+pd.Timedelta('5min')
def spy_at(ts):
    s=spy[spy.tend<=ts]
    return s.c.iloc[-1] if len(s) else np.nan
t['spy_e']=[spy_at(x) for x in t.entry_time]; t['spy_x']=[spy_at(x) for x in t.exit_time]
t['spy_open']=t.date.map(op); t['spy_e_fo']=(t.spy_e/t.spy_open-1)*100
t['spy_move']=(t.spy_x/t.spy_e-1)*100*t.side   # + = market moved with the trade
t.to_pickle('t.pkl'); day.to_pickle('day.pkl'); print(len(t)); print(day.round(2).to_string())
