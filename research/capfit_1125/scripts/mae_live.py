import pandas as pd, numpy as np, pyarrow.dataset as pads
from pathlib import Path
TZ="America/New_York"; HIST=Path("/home/user/MCF/data/cache_hist/1Min")
t=pd.read_parquet('all_trades.parquet'); S=[l.strip() for l in open('setups.csv')]
t=t[t.strategy.isin(S)&(t.date<='2026-11-24')].copy()
t['side_n']=np.where(t.side.astype(str).str.lower().isin(['1','long','buy']),1,-1)
t['risk']=(t.entry-t.stop).abs()
t['et']=pd.to_datetime(t.entry_time,utc=True,format='mixed').dt.tz_convert(TZ).dt.floor('min')
t['xt']=pd.to_datetime(t.exit_time,utc=True,format='mixed').dt.tz_convert(TZ).dt.floor('min')
G=pd.read_parquet('/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/pyramid/G/live_bars.parquet')
G.index=pd.DatetimeIndex(G.index).tz_convert(TZ)
mae={}
for sym,g in t.groupby('symbol'):
    bs=[]
    p=HIST/f'{sym}.parquet'
    if p.exists():
        f=pads.field("__index_level_0__")
        try:
            b=pads.dataset(str(p),format='parquet').to_table(filter=f>=pd.Timestamp('2026-10-06',tz=TZ),columns=['high','low','__index_level_0__']).to_pandas()
            if '__index_level_0__' in b.columns: b=b.set_index('__index_level_0__')
            b.index=pd.DatetimeIndex(b.index).tz_convert(TZ); bs.append(b)
        except Exception as e: print('ERR',sym,e)
    gb=G[G.symbol==sym][['high','low']]
    if len(gb): bs.append(gb)
    if not bs: continue
    b=pd.concat(bs); b=b[~b.index.duplicated()].sort_index()
    for r in g.itertuples():
        w=b.loc[(b.index>r.et)&(b.index<=r.xt)]
        if r.xt<=r.et: mae[r.Index]=0.0; continue
        if not len(w): continue
        adv=(r.entry-w.low.min()) if r.side_n>0 else (w.high.max()-r.entry)
        mae[r.Index]=-max(0,adv)/r.risk if r.risk>0 else np.nan
t['mae']=pd.Series(mae)
t[['strategy','symbol','date','side_n','r','risk','exit_reason','mae']].to_parquet('live_mae.parquet')
print(len(t), t.mae.notna().sum())
