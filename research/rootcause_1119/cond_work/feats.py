"""Attach point-in-time market state to trades. Educational only."""
import pickle, numpy as np, pandas as pd
G=pickle.load(open("grids.pkl","rb")); ST=pd.read_pickle("compass.pkl")
WP=ST.pivot(index="date",columns="T",values="W"); CPS=np.array(WP.columns)
beta=pd.read_csv("beta.csv",index_col=0).iloc[:,0]
def feats(df, date="date", em="em", xm="xm"):
    out=[]
    for d,e,x,sym,side in zip(df[date],df[em],df[xm],df.symbol,df.side):
        s=G["SPY"].get(d); r={}
        b=beta.get(sym,1.0); ms=int(side)*(-1 if b<-0.3 else 1)
        r["mkt_side"]=ms; r["inverse"]=b<-0.3
        if s is None or not np.isfinite(e): out.append(r); continue
        i=int(min(max(e-571,0),389)); j=int(min(max((x if np.isfinite(x) else 955)-571,i),389))
        o=s["o"]; c=s["c"]
        r["spy_fo"]=(c[i]/o-1)*100; r["spy_30"]=(c[i]/c[max(i-30,0)]-1)*100
        r["spy_vw"]=(c[i]/s["vw"][i]-1)*100
        r["spy_after"]=(c[j]/c[i]-1)*100              # SPY move entry->exit (not point-in-time; diagnosis only)
        r["spy_oc"]=(c[-1]/o-1)*100 if s["last"]>=385 else np.nan
        r["spy_rest"]=(c[-1]/c[i]-1)*100 if s["last"]>=385 else np.nan
        r["spy_rng"]=(np.nanmax(s["h"][:i+1])-np.nanmin(s["l"][:i+1]))/o*100   # range so far today (vol proxy)
        k=np.searchsorted(CPS,e,side="right")-1
        r["W"]=WP.loc[d,CPS[k]] if (k>=0 and d in WP.index) else np.nan
        out.append(r)
    f=pd.DataFrame(out,index=df.index)
    df=pd.concat([df,f],axis=1)
    a=df.W*df.mkt_side
    df["cmp"]=np.where(df.W.abs()==2, np.where(a>0,"aligned","AGAINST"), np.where(df.W.isna(),"na","unconf"))
    df["mkt_with"]=df.spy_after*df.mkt_side       # + = market moved in the trade's favour after entry
    return df
def mins(t):  # HHMM int -> minutes
    return (t//100)*60+t%100
