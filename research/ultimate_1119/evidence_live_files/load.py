import sqlite3, glob, os, sys, pandas as pd
sys.path.insert(0, '/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/ult')
os.chdir('/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/ult')
from mcf.costs import with_cost_r
J='/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/ev1119/j'
fr=[]
for f in sorted(glob.glob(J+'/*.db')):
    acct=os.path.basename(f)[:-3].replace('mcf-data-','').replace('mcf-data','primary')
    c=sqlite3.connect(f)
    d=pd.read_sql("select t.* from trades t join runs r on r.id=t.run_id where r.kind='paper' and t.exit_time is not null",c)
    d['account']=acct; fr.append(d)
df=pd.concat(fr,ignore_index=True)
df=with_cost_r(df)
df=df[df.r_multiple.notna()]
df.drop(columns=['meta']).to_parquet(J+'/../w/trades.parquet')
print(len(df), df.symbol.nunique(), df.groupby('date').symbol.nunique().describe())
print(df.groupby('account').r_multiple.agg(['count','mean','sum']))
