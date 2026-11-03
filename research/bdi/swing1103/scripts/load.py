import json, sqlite3, pickle, numpy as np, pandas as pd
S='/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/swing1103/data/'
NY='America/New_York'
B=pickle.load(open(S+'bars.pkl','rb')); H=pickle.load(open(S+'hist5.pkl','rb'))
def ts(x): return pd.Timestamp(x).tz_convert(NY)
c=sqlite3.connect(S+'journal.db')
tr=pd.read_sql("select * from trades where date='2026-11-03'",c)
od=pd.read_sql("select * from orders where created_at>='2026-11-03'",c)
st=json.load(open(S+'status.json'))
rows=[]
for _,r in tr.iterrows():
    rows.append(dict(sym=r.symbol,strat=r.strategy,side=r.side,qty=r.shares,entry=r.entry,stop=r.stop,
      et=ts(r.entry_time),xt=ts(r.exit_time),exit=r.exit,reason=r.exit_reason,r_j=r.r_multiple,pnl=r.pnl,slip=r.slip_bps,
      meta=r.meta))
openp={p['symbol']:p for p in st['positions']}
for _,o in od[od.status=='submitted'].iterrows():
    p=openp[o.symbol]
    rows.append(dict(sym=o.symbol,strat=o.strategy,side=o.side,qty=o.qty,entry=p['entry'],stop=o.stop,
      et=ts(o.created_at),xt=pd.NaT,exit=np.nan,reason='open',r_j=np.nan,pnl=np.nan,slip=np.nan,meta=o.meta))
T=pd.DataFrame(rows)
T['risk']=(T.entry-T.stop).abs()*T.qty
# beta vs SPY from 5-min returns (20 sessions), excluding overnight
def r5(df):
    s=df.close; d=s.index.date
    r=s.pct_change(); r[pd.Series(d,index=s.index).ne(pd.Series(d,index=s.index).shift())]=np.nan
    return r
spy=r5(H['SPY'])
beta={}
for k,v in H.items():
    x=pd.concat([r5(v),spy],axis=1,keys=['y','x']).dropna()
    beta[k]=np.cov(x.y,x.x)[0,1]/x.x.var()
T['beta']=T.sym.map(beta)
def px(sym,t):
    """close of last 1-min bar that finished by t"""
    b=B[sym]; s=b.close[b.index<=t-pd.Timedelta(minutes=1)]
    return s.iloc[-1] if len(s) else np.nan
