"""Part A: rank LONG setups live by avg R (LR8). Educational only - not financial advice."""
import numpy as np, pandas as pd
t = pd.read_pickle("live_ext.pkl"); L = t[t.side == 1].copy()
def ct(g):
    m = g.r.mean(); d = g.groupby("date").agg(s=("r","sum"), n=("r","size"))
    v = ((d.s - m*d.n)**2).sum(); return m/np.sqrt(v)*len(g) if v > 0 else np.nan
rows=[]
for s,g in L.groupby("strategy"):
    if len(g) < 20: continue
    day=g.groupby("date").r.sum(); tot=g.r.sum(); best=day.idxmax()
    rows.append(dict(setup=s,n=len(g),sess=day.size,avg=g.r.mean(),wo=g[g.date!=best].r.mean(),
        share=day.max()/tot if tot>0 else np.nan,best=best,t=ct(g),win=(g.r>0).mean(),tot=tot,
        accts=",".join(sorted(g.account.unique()))))
x=pd.DataFrame(rows).sort_values("avg",ascending=False)
pd.set_option("display.width",250); pd.set_option("display.max_rows",400)
print("long setups >=20 trades:",len(x)," positive avg:",(x.avg>0).sum()," positive wo:",(x.wo>0).sum())
print(x.head(30).round(3).to_string(index=False))
x.to_csv("live_long_rank.csv",index=False)
print("all longs pooled", len(L), L.r.mean(), " shorts", t[t.side==-1].r.mean())
