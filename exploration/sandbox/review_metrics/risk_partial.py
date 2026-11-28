import sys, numpy as np, pandas as pd
from scipy import stats
T=sys.argv[1]; t=pd.read_parquet(f"{T}/live.parquet")
t["wk"]=pd.to_datetime(t.date).dt.to_period("W-FRI").astype(str)
def f(g):
    d=g.groupby("date").r.sum(); n=g.groupby("date").size()
    return pd.Series({"n":len(g),"worst":d.min(),"dsd":d.std(ddof=1),"lpd":len(g)/len(d),
        "worst_pl":(d/n).min(),"dsd_pl":(d/np.sqrt(n)).std(ddof=1)})
for lab,tt in [("full",t),("from1023",t[t.date>="2026-10-23"])]:
  rows=[]
  for w in sorted(tt.wk.unique()):
    past,nxt=tt[tt.wk<w],tt[tt.wk==w]
    if past.date.nunique()<5: continue
    a=past.groupby("strategy").apply(f); a=a[a.n>=20]; b=nxt.groupby("strategy").apply(f); b=b[b.n>=5]
    j=a.join(b,rsuffix="_n",how="inner")
    if len(j)<20: continue
    # partial: residualize ranks on lpd
    def part(x,y,z):
        rx,ry,rz=[stats.rankdata(v) for v in (j[x],j[y],j[z])]
        ex=rx-np.polyval(np.polyfit(rz,rx,1),rz); ey=ry-np.polyval(np.polyfit(rz,ry,1),rz); return np.corrcoef(ex,ey)[0,1]
    jj=j.dropna()
    rows.append({"wk":w,"N":len(jj),"worst->worst|lpd":part("worst","worst_n","lpd") if True else 0,
       "dsd->dsd|lpd":(lambda: (lambda j2: None)(0))() , "wpl->wpl":stats.spearmanr(jj.worst_pl,jj.worst_pl_n).correlation,
       "dsdpl->dsdpl":stats.spearmanr(jj.dsd_pl,jj.dsd_pl_n).correlation})
    j=jj; rows[-1]["dsd->dsd|lpd"]=part("dsd","dsd_n","lpd")
  r=pd.DataFrame(rows).set_index("wk"); print(lab); print(r.round(2).to_string())
  for c in r.columns[1:]:
    x=r[c].dropna(); print(f"  {c:18s} {x.mean():6.3f} (t {x.mean()/(x.std(ddof=1)/np.sqrt(len(x))):5.2f}) folds {len(x)}")
A=["GEN-261023-06","GEN-261022-05","GEN-261023-07","GEN-261026-07","GEN-261020-09","NM-RWN5","GEN-261021-01","GEN-261026-03"]
B=["NM-RWN5","GEN-261021-01","GEN-261027-01","GEN-261023-09","GEN-261029-06"]
u=t[t.date>="2026-10-23"]
for nm,L in [("A",A),("B",B)]:
    s=u[u.strategy.isin(L)].groupby("strategy").apply(f); print(nm); print(s[["n","lpd","worst","worst_pl"]].round(2).to_string()); print("  mean lpd",round(s.lpd.mean(),1),"mean worst",round(s.worst.mean(),1),"mean worst/lot",round(s.worst_pl.mean(),2))
