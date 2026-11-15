"""Sizing-up study 2026-11-15: load every live journal (run_id=1). Educational only - not financial advice."""
import sqlite3,pandas as pd,glob,os
D=os.environ.get('MCF_JOURNALS', 'journals')   # folder of <branch>.db = journal.db of each mcf-data* branch
def load():
    out=[]
    for f in glob.glob(D+'/*.db'):
        acct=os.path.basename(f)[:-3].replace('mcf-data-','') ; acct='primary' if acct=='mcf-data' else acct
        c=sqlite3.connect(f)
        t=pd.read_sql("select symbol,strategy,side,date,entry_time,exit_time,entry,stop,shares,pnl,pnl_adj,r_multiple,exit_reason,meta from trades where run_id=1 and exit is not null",c)
        t['acct']=acct; out.append(t)
    t=pd.concat(out); t=t[t.shares>0]
    t['risk']=(t.entry-t.stop).abs()*t.shares
    t=t[t.risk>0]
    t['R']=t.pnl_adj.fillna(t.pnl)/t.risk
    t['notional']=t.entry*t.shares
    return t
