"""W60 compass readings per (date, 15-min mark): history = production backfill logic (l3leash/state15: SPY/QQQ/IWM
1-min + lab breadth_open), live = recorded compass CSVs, missing days = proxy (breadth vote replaced by the
QQQ/IWM-agree vote sign). Codes +2 UP-conf, +1 lean up, 0, -1 lean down, -2 DOWN-conf. Educational only."""
import glob, pickle, numpy as np, pandas as pd
LOCK=("2024-11-01","2025-02-28")
G=pickle.load(open("grids.pkl","rb"))
CPS=list(range(585,931,15))
ctx=pd.concat(pd.read_parquet(p) for p in sorted(glob.glob("/home/user/MCF/research/history2y/data/context/month=*.parquet")))
ctx["date"]=pd.to_datetime(ctx.date).dt.strftime("%Y-%m-%d"); ctx["T"]=(ctx.tod//100)*60+ctx.tod%100
ctx=ctx[~ctx.date.between(*LOCK)]
br=ctx.set_index(["date","T"]).breadth_open
rows=[]
for d,x in G["SPY"].items():
    q=G["QQQ"].get(d); iw=G["IWM"].get(d)
    for T in CPS:
        i=T-571
        if i>x["last"]: continue
        fo=x["c"][i]/x["o"]-1; vw=x["c"][i]/x["vw"][i]-1
        qf=q["c"][i]/q["o"]-1 if q else np.nan; jf=iw["c"][i]/iw["o"]-1 if iw else np.nan
        b=br.get((d,min(T,900)),np.nan) if T!=585 else 0.5
        rows.append(dict(date=d,T=T,fo=fo,vw=vw,qfo=qf,ifo=jf,b=b))
st=pd.DataFrame(rows).sort_values(["date","T"]).reset_index(drop=True)
sg=lambda a: np.nan_to_num(np.sign(np.asarray(a,float))).astype(int)
st["s"]=sg(st.fo)
agree=np.where((st.s==sg(st.qfo))&(st.s==sg(st.ifo)),st.s,0)
bv=np.where(st.b>0.5,1,np.where(st.b<0.5,-1,0))
piv=st.pivot(index="date",columns="T",values="s")
pW=np.zeros(len(st),int); nm=np.zeros(len(st),int)
for T in CPS:
    mk=[t for t in piv.columns if T-60<t<=T]; sub=piv[mk]
    same=sub.eq(sub[T],axis=0).all(axis=1)&(sub[T]!=0); i=(st["T"]==T).values
    pW[i]=np.where(same.reindex(st.date[i]).values,piv[T].reindex(st.date[i]).values,0); nm[i]=len(mk)
def w60(v):
    return np.where((v>=4)&(pW==1)&(nm>=2),2,np.where(v>=2,1,np.where((v<=-4)&(pW==-1)&(nm>=2),-2,np.where(v<=-2,-1,0))))
st["W_real"]=np.where(st.b.notna(), w60(st.s+sg(st.vw)+bv+agree+pW), np.nan)
st["W_proxy"]=w60(st.s+sg(st.vw)+np.where(agree!=0,agree,0)+agree+pW)
# live CSVs
M={"UP-confirmed":2,"leaning up":1,"mixed":0,"neutral":0,"leaning down":-1,"DOWN-confirmed":-2}
lv=[]
for f in glob.glob("cmp_*.csv"):
    c=pd.read_csv(f)
    if len(c)<5: continue
    c["T"]=c["T"].str[:2].astype(int)*60+c["T"].str[3:].astype(int); c["W_live"]=c.w60.map(M)
    lv.append(c[["date","T","W_live"]])
lv=pd.concat(lv); st=st.merge(lv,on=["date","T"],how="left")
st["W"]=st.W_live.where(st.W_live.notna(), st.W_real.where(st.W_real.notna(), st.W_proxy))
st["Wsrc"]=np.where(st.W_live.notna(),"live",np.where(st.W_real.notna(),"backfill","proxy"))
# today: recorded fact (task/owner) - DOWN-confirmed from 11:15; keep proxy before
k=(st.date=="2026-11-19")&(st["T"]>=675)&(st["T"]<=735); st.loc[k,"W"]=-2; st.loc[k,"Wsrc"]="owner-mark"
st.to_pickle("compass.pkl")
h=st[st.W_real.notna()]
print("proxy vs real agreement (history):", (h.W_proxy==h.W_real).mean().round(3), " conf-DOWN real->proxy", pd.crosstab(h.W_real,h.W_proxy).to_string())
print(st.groupby("Wsrc").date.nunique())
print(st[st.date=="2026-11-19"][["T","fo","W_proxy","W","Wsrc"]].to_string())
lvj=st[st.W_live.notna()&st.W_real.notna()]; print("live vs backfill agree", (lvj.W_live==lvj.W_real).mean() if len(lvj) else None)
