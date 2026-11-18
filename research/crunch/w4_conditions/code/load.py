"""W4 trade loader. Educational only - not financial advice. Live run (run_id 1) of every mcf-data* journal."""
import sqlite3, pandas as pd, numpy as np, os
J=os.environ.get("MCF_JDIR","j")
ACC=['primary','ondeck','testA','testB','testC','testD','testE','testF','gen','graveyard']
def load():
    out=[]
    for a in ACC:
        c=sqlite3.connect(f'{J}/{a}.db')
        d=pd.read_sql('select id,symbol,strategy,side,date,signal_time,entry_time,entry,stop,target,exit_time,exit,exit_reason,shares,pnl,pnl_adj,mfe_r,mae_r from trades where run_id=1',c)
        d['acct']=a; out.append(d)
    t=pd.concat(out,ignore_index=True)
    t=t[(t.shares>0)&(t.pnl_adj.notna())]
    t['risk']=(t.entry-t.stop).abs()*t.shares
    t=t[t.risk>0]
    t['R']=t.pnl_adj/t.risk
    t['sig']=pd.to_datetime(t.signal_time.fillna(t.entry_time),utc=True,format='mixed')
    return t
if __name__=='__main__':
    t=load()
    print(len(t), t.date.min(), t.date.max())
    top=t.groupby('strategy').agg(n=('R','size'),R=('R','sum'),avg=('R','mean'),days=('date','nunique'),accts=('acct',lambda s:','.join(sorted(set(s))))).sort_values('n',ascending=False)
    pd.set_option('display.width',250); pd.set_option('display.max_colwidth',60)
    print(top.head(40))
    t.to_pickle('trades.pkl')
