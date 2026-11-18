import sys, sqlite3, pandas as pd, numpy as np
S=sys.argv[1]
ARCH=set(open(f"{S}/arch.txt").read().split()); TUNE=set("NS3-failed-vwap-reclaim-short-FD MF1-945-flowsell-vwapup-FD MF3-open-flowsell-rsi5hi-FD".split())
c=sqlite3.connect(f"{S}/j/mcf-data-graveyard.db")
t=pd.read_sql("select strategy,date,entry,stop,shares,pnl_adj,r_multiple from trades where run_id=1 and exit_time is not null",c)
risk=(t.entry-t.stop).abs()*t.shares.abs(); t["R"]=np.where(t.pnl_adj.notna()&(risk>0),t.pnl_adj/risk,t.r_multiple)
t["grp"]=np.where(t.strategy.isin(ARCH),"archive",np.where(t.strategy.isin(TUNE),"tune","keep/other"))
d=sorted(t.date.unique()); last10=d[-11:-1]  # 11-04..11-17 (pre-bench)
x=t[t.date.isin(last10)]
g=x.groupby("grp").agg(n=("R","size"),R=("R","sum"),usd=("pnl_adj","sum"))
g["per_session_n"]=g.n/10; g["per_session_R"]=g.R/10; g["per_session_usd"]=g.usd/10
print(g.round(1)); tot=x.agg({"R":"sum","pnl_adj":"sum"}); print("all", len(x)/10, (tot/10).round(1).to_dict())
w=t.groupby("grp").agg(n=("R","size"),R=("R","sum"),usd=("pnl_adj","sum")); print("whole GY:\n",w.round(1)); print("sessions",len(d),d[0],d[-1])
s=pd.read_sql("select day,strategy,count(*) n from signals where run_id=1 group by 1,2",c)
s["grp"]=np.where(s.strategy.isin(ARCH),"archive","other"); print(s[s.day.isin(last10)].groupby("grp").n.sum()/10)
print("max concurrent per-day archive share of trades", (x.grp=="archive").mean().round(3))
