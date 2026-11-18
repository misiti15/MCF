"""Journal loader for W1-redteam. Educational only - not financial advice. Set MCF_JDIR to a folder of journal.db copies
(primary.db, ondeck.db, testA..testF.db, gen.db, graveyard.db from the mcf-data* state branches)."""
import os, sqlite3, pandas as pd, numpy as np
S=os.environ.get("MCF_JDIR","./j/").rstrip("/")+"/"
ACC=['primary','ondeck','testA','testB','testC','testD','testE','testF','gen','graveyard']
def load(acc, run=1):
    c=sqlite3.connect(S+acc+'.db')
    df=pd.read_sql(f'select * from trades where run_id={run}',c)
    df['acct']=acc
    risk=(df.entry-df.stop).abs()*df.shares
    df['risk']=risk
    df['R']=df.pnl_adj/risk
    df['Rraw']=df.pnl/risk
    df['cost']=df.Rraw-df.R
    return df
def all_(run=1):
    return pd.concat([load(a,run) for a in ACC],ignore_index=True)

if __name__=='__main__':
    all_().to_pickle('all.pkl')
