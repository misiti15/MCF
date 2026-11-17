import sqlite3, glob, pandas as pd
rows=[]
for f in glob.glob("j_*.db"):
    acct=f[2:-3]; c=sqlite3.connect(f)
    d=pd.read_sql("select symbol,strategy,side,date,entry_time,exit_time,entry,stop,shares,pnl,pnl_adj,r_multiple,exit_reason from trades where run_id=1 and exit_time is not null",c)
    d["branch"]=acct; rows.append(d); c.close()
T=pd.concat(rows,ignore_index=True)
pa=T.pnl_adj.fillna(T.pnl.fillna(0)); risk=(T.entry-T.stop).abs()*T.shares
T["R"]=(pa/risk).where(risk>0,T.r_multiple.fillna(0))
T.to_parquet("live_all.parquet"); print(len(T),T.date.min(),T.date.max()); print(T.side.value_counts()); print(T.groupby("branch").size())
