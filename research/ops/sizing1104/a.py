import sqlite3,pandas as pd,numpy as np
fr=[]
for b,a in [("mcf-data","Primary"),("mcf-data-testing","Testing 1"),("mcf-data-testing2","Testing 2"),("mcf-data-graveyard","Graveyard")]:
    c=sqlite3.connect(f"{b}.db")
    d=pd.read_sql("select * from trades where run_id=1 and exit is not null",c); d["acct"]=a; fr.append(d)
t=pd.concat(fr)
t["pnl_adj"]=t.pnl_adj.fillna(t.pnl)
risk=(t.entry-t.stop).abs()*t.shares
t["R"]=t.pnl_adj/risk
t=t[np.isfinite(t.R)]
g=t.groupby("strategy").R.agg(["count","mean"])
g["shrunk"]=g["mean"]*g["count"]/(g["count"]+20)
g=g[g["count"]>=20].sort_values("shrunk",ascending=False)
print(g.head(8))
t.to_pickle("t.pkl")
print(sorted(t.date.unique())[-12:])
