import pandas as pd, numpy as np
a=pd.read_parquet("../mech2-l3w/spy1m.parquet"); a.index=pd.DatetimeIndex(a.index).tz_convert("America/New_York")
b=pd.read_parquet("spy_new.parquet"); b=b.set_index(pd.DatetimeIndex(b.ts).tz_convert("America/New_York"))[["open","high","low","close"]].astype(float)
s=pd.concat([a[["open","high","low","close"]],b]); s=s[~s.index.duplicated(keep="first")].sort_index()
s.to_parquet("spy1m_all.parquet")
s["date"]=s.index.strftime("%Y-%m-%d"); s["mn"]=s.index.hour*60+s.index.minute
rows=[]
for d,g in s.groupby("date"):
    g=g.set_index("mn")
    if 589 not in g.index: continue
    rth=g.loc[570:959]
    c950=g.close.loc[589]; c16=rth.close.iloc[-1]
    rows.append(dict(date=d,c950=c950,c16=c16,o=rth.open.iloc[0],r950=(c16/c950-1)*100,roc=(c16/rth.open.iloc[0]-1)*100))
D=pd.DataFrame(rows)
D["dtype"]=np.where(D.r950>0.25,"up",np.where(D.r950<-0.25,"down","quiet"))
D["dtype_oc"]=np.where(D.roc>0.25,"up",np.where(D.roc<-0.25,"down","quiet"))
D.to_parquet("spyday.parquet"); print(D.tail(30).to_string()); print(D.dtype.value_counts())
