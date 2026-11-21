import pandas as pd, numpy as np
from idx import feats
TZ="America/New_York"
parts=[]
for nm in ['SPY','QQQ','IWM']:
    b=pd.read_parquet(f'live_{nm}.parquet'); b.index=pd.DatetimeIndex(b.index).tz_convert(TZ); b=b.sort_index()
    hm=b.index.hour*100+b.index.minute; b=b[(hm>=930)&(hm<1600)].copy(); b['date']=b.index.date.astype(str)
    if nm=='SPY':
        d=b.groupby('date').agg(o=('open','first'),h=('high','max'),l=('low','min'),c=('close','last'))
        d['pc']=d.c.shift(); tr=np.maximum(d.h-d.l,np.maximum((d.h-d.pc).abs(),(d.l-d.pc).abs()))
        d['atr14p']=(tr.rolling(14).mean()/d.c*100).shift(); d['ret5d']=(d.c.shift()/d.c.shift(6)-1)*100
        d[['atr14p','ret5d']].to_parquet('spy_daily_live.parquet')
    parts.append(feats(b[b.date>='2026-10-01'],nm.lower()+'_').set_index(['date','tod']))
F=pd.concat(parts,axis=1).reset_index(); F.to_parquet('idx_feats_live.parquet'); print(F.shape)
