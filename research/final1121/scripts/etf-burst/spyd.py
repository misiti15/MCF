from idx import load
import pandas as pd, numpy as np
b1=load("/home/user/MCF/data/cache_hist/1Min/SPY.parquet"); b2=load("/home/user/MCF/data/cache_fresh/1Min/SPY.parquet")
b=pd.concat([b2[b2.date<"2024-09-16"],b1[b1.date>="2024-09-16"]])
d=b.groupby('date').agg(o=('open','first'),h=('high','max'),l=('low','min'),c=('close','last'))
d['pc']=d.c.shift(); tr=np.maximum(d.h-d.l,np.maximum((d.h-d.pc).abs(),(d.l-d.pc).abs()))
d['atr14p']=(tr.rolling(14).mean()/d.c*100).shift()   # prior days only (note: gap across locked block for 2025-03 rows)
d['ret5d']=(d.c.shift()/d.c.shift(6)-1)*100
d[['atr14p','ret5d']].to_parquet('spy_daily.parquet'); print(d[['atr14p','ret5d']].describe())
