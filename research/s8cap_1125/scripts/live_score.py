"""S8-CAP live replay scoring. Educational only - not financial advice."""
import pandas as pd, numpy as np, math
pd.set_option("display.width",250); pd.set_option("display.max_rows",400)
C=["C6L","C6N","C8L","C8N","C10L","C10N","CSL","CSN","K4N","NOW","ACT"]
def t(x):
    x=np.asarray(x,float); return x.mean()/(x.std(ddof=1)/math.sqrt(len(x))) if len(x)>2 and x.std()>0 else np.nan
rows=[];srows=[]
for book in ("RAW","NEUTRAL"):
    L=pd.read_parquet(f"live_{book}.parquet")
    AD=L.groupby(["cfg","account","date"]).R.sum().unstack(0).fillna(0)
    for scope,m in (("Primary",AD.index.get_level_values(0)=="primary"),("Primary>=10-29",(AD.index.get_level_values(0)=="primary")&(AD.index.get_level_values(1)>="2026-10-29")),("All accts",np.ones(len(AD),bool)),("All ex gen/livelab",~AD.index.get_level_values(0).isin(["gen","livelab"]))):
        a=AD[m]
        for c in C:
            d=a[c]-a["REF"]
            fl=L[(L.cfg==c)&(L.capm>=0)]
            fl=fl[fl.set_index(["account","date"]).index.isin(a.index)]
            rows.append(dict(book=book,scope=scope,cfg=c,days=len(a),R_ref=round(a.REF.sum(),1),R=round(a[c].sum(),1),dR=round(d.sum(),1),t=round(t(d),2),
              top_day_share=round(d.max()/d[d>0].sum(),2) if (d>0).any() else np.nan, dR_wo_best=round(d.sum()-d.max(),1),
              worst_ref=round(a.REF.min(),1),worst=round(a[c].min(),1),w5_ref=round(a.REF.nsmallest(5).mean(),1),w5=round(a[c].nsmallest(5).mean(),1),
              cap_fires=len(fl),better_days=int((d>1e-9).sum()),worse_days=int((d<-1e-9).sum())))
    S=L.groupby(["cfg","strategy","account","date"]).R.sum().unstack(0).fillna(0)
    for c in ["C6L","C8L","C10L","CSL","C8N"]:
        d=(S[c]-S["REF"]).groupby(level=0).sum()
        srows.append(dict(book=book,cfg=c,setups_better=int((d>0.5).sum()),setups_worse=int((d<-0.5).sum()),worse_sum=round(d[d<0].sum(),1),worst_setup=d.idxmin()[:30],worst_setup_dR=round(d.min(),1),best_setup=d.idxmax()[:30],best_dR=round(d.max(),1),n_worse_gt10=int((d<-10).sum())))
R=pd.DataFrame(rows); R.to_csv("live_results.csv",index=False); print(R.to_string(index=False))
print(pd.DataFrame(srows).to_string(index=False))
# primary per-setup for C8L / CSL / C10L
for book in ("RAW","NEUTRAL"):
    L=pd.read_parquet(f"live_{book}.parquet"); L=L[L.account=="primary"]
    S=L.groupby(["cfg","strategy"]).R.sum().unstack(0)
    print(book,"primary per setup"); print((S[["C6L","C8L","C10L","CSL","C8N"]].sub(S.REF,axis=0)).round(1).assign(REF=S.REF.round(1)).to_string())
