"""Index-state features at each 5-min decision time (bar close T, 14:00-15:00) from SPY/QQQ/IWM 1-min bars.
Locked block 2024-11-01..2025-02-28 never read. Educational only - not financial advice."""
import numpy as np, pandas as pd, pyarrow.dataset as pads, sys
TZ="America/New_York"; LOCK=("2024-11-01","2025-02-28")
def load(path, filt=True):
    d=pads.dataset(path,format="parquet"); f=pads.field("__index_level_0__")
    if filt:
        b=d.to_table(filter=(f<pd.Timestamp(LOCK[0],tz=TZ))|(f>=pd.Timestamp("2025-03-01",tz=TZ))).to_pandas()
    else: b=d.to_table().to_pandas()
    if "__index_level_0__" in b.columns: b=b.set_index("__index_level_0__")
    b.index=pd.DatetimeIndex(b.index).tz_convert(TZ); b=b.sort_index()
    hm=b.index.hour*100+b.index.minute; b=b[(hm>=930)&(hm<1600)].copy()
    b["date"]=b.index.date.astype(str)
    assert not ((b.date>=LOCK[0])&(b.date<=LOCK[1])).any()
    return b
def feats(b, pre):
    out=[]
    for d,g in b.groupby("date"):
        hm=(g.index.hour*100+g.index.minute).to_numpy()
        o=g.open.iloc[0]; c=g.close.to_numpy(); h=g.high.to_numpy(); l=g.low.to_numpy(); v=g.volume.to_numpy()
        tp=(h+l+c)/3; cpv=np.cumsum(tp*v); cv=np.cumsum(v)
        for T in range(1355,1505,5):
            if T%100>=60: continue
            k=np.flatnonzero(hm<T)
            if not len(k): continue
            k=k[-1]
            def at(t):
                j=np.flatnonzero(hm<t); return c[j[-1]] if len(j) else np.nan
            hi=h[:k+1].max(); lo=l[:k+1].min()
            # minutes since day low
            jl=int(np.argmin(l[:k+1])); 
            r=dict(date=d,tod=T,**{
              pre+"fo":(c[k]/o-1)*100, pre+"vw":(c[k]/(cpv[k]/cv[k])-1)*100,
              pre+"s950":(c[k]/at(950)-1)*100, pre+"r60":(c[k]/at(T-100)-1)*100,
              pre+"r15":(c[k]/at(T-15 if T%100>=15 else T-55)-1)*100,
              pre+"pos":(c[k]-lo)/(hi-lo) if hi>lo else 0.5,
              pre+"lowage":k-jl,
              pre+"s1300":(c[k]/at(1300)-1)*100})
            out.append(r)
    return pd.DataFrame(out)
if __name__=="__main__":
    parts=[]
    for nm in ["SPY","QQQ","IWM"]:
        b1=load(f"/home/user/MCF/data/cache_hist/1Min/{nm}.parquet")
        b2=load(f"/home/user/MCF/data/cache_fresh/1Min/{nm}.parquet")
        b2=b2[(b2.date>="2023-01-03")&(b2.date<="2024-09-13")]
        b1=b1[b1.date>="2024-09-16"]
        f=feats(pd.concat([b2,b1]), nm.lower()+"_")
        parts.append(f.set_index(["date","tod"]))
    F=pd.concat(parts,axis=1).reset_index()
    F.to_parquet("idx_feats.parquet"); print(F.shape, F.date.min(), F.date.max())
