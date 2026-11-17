import pandas as pd, yaml
T=pd.read_parquet("live_all.parquet"); D=pd.read_parquet("spyday.parquet").set_index("date")
names=yaml.safe_load(open("../wt-wb-upday/config/setup_names.yaml"))
S=T[T.side==-1].copy(); S["dt"]=S.date.map(D.dtype)
rows=[]
for k,g in S.groupby("strategy"):
    n=len(g); 
    if n<60: continue
    bd=g.groupby("date").R.sum(); best=bd.idxmax(); wo=g[g.date!=best].R.mean()
    r=dict(id=k,name=(names.get(k) or {}).get("name",""),trades=n,sessions=g.date.nunique(),avg=g.R.mean(),wo=wo,best_share=bd.max()/g.R.sum() if g.R.sum()>0 else None,
           accts=",".join(sorted(g.branch.str.replace("mcf-data-","").str.replace("mcf-data","primary").unique())))
    for t in ("up","down","quiet"):
        x=g[g.dt==t]; r[t]=x.R.mean(); r["n_"+t]=len(x); r["s_"+t]=x.date.nunique()
    rows.append(r)
X=pd.DataFrame(rows).sort_values("trades",ascending=False)
X.to_csv("stepa_all.csv",index=False)
Q=X[(X.avg>0)&(X.wo>0)]
pd.set_option("display.width",250); print(Q.head(12).round(3).to_string()); print(len(X),len(Q))
print("day type counts in live window:", D.loc["2026-10-06":].dtype.value_counts().to_dict())
