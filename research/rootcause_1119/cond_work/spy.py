"""SPY/QQQ/IWM 1-min day grids: history cache (locked block dropped) + live window + today. Educational only."""
import numpy as np, pandas as pd
LOCK=("2024-11-01","2025-02-28")
def grid(b):
    b=b.copy(); b.index=pd.to_datetime(b.index)
    if b.index.tz is None: b.index=b.index.tz_localize("America/New_York")
    b=b.tz_convert("America/New_York"); m=b.index.hour*60+b.index.minute
    b=b[(m>=570)&(m<960)]; m=(b.index.hour*60+b.index.minute).values-570
    d=b.index.strftime("%Y-%m-%d").values; D={}
    for day in pd.unique(d):
        if LOCK[0]<=day<=LOCK[1]: continue
        k=d==day; mm=m[k]
        C=np.full(390,np.nan); C[mm]=b.close.values[k]; C=pd.Series(C).ffill().values
        H=np.full(390,np.nan); H[mm]=b.high.values[k]; L=np.full(390,np.nan); L[mm]=b.low.values[k]
        TP=np.zeros(390);V=np.zeros(390); TP[mm]=(b.high.values[k]+b.low.values[k]+b.close.values[k])/3; V[mm]=b.volume.values[k]
        D[day]=dict(o=float(b.open.values[k][0]),c=C,h=H,l=L,vw=np.cumsum(TP*V)/np.maximum(np.cumsum(V),1),last=int(mm.max()))
    return D
def load(sym):
    h=pd.read_parquet(f"/home/user/MCF/data/cache_hist/1Min/{sym}.parquet")[["open","high","low","close","volume"]]
    D=grid(h)
    for f in ["today/live_window.parquet","today/bars.parquet"]:
        x=pd.read_parquet(f); x=x[x.symbol==sym].set_index("ts")[["open","high","low","close","volume"]]
        for k,v in grid(x).items():
            if k not in D: D[k]=v
    assert not any(LOCK[0]<=d<=LOCK[1] for d in D)
    return D
