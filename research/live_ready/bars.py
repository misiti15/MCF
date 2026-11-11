# LIVE-READY 2026-11-11 (research only). Reads journal.db copies of every data branch from a scratch folder (S).
import pandas as pd, numpy as np
S='/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad'
F={'2026-11-05':f'{S}/mh1105/cov/days/2026-11-05/bars.parquet','2026-11-06':f'{S}/mh1106/cov/days/2026-11-06/bars.parquet',
   '2026-11-09':f'{S}/mh1109/cov/days/2026-11-09/bars.parquet','2026-11-10':f'{S}/mh1110/cov/days/2026-11-10/bars.parquet'}
def load():
    out=[]
    for d,f in F.items():
        b=pd.read_parquet(f)
        if 'ts' not in b: b=b.reset_index().rename(columns={'timestamp':'ts'})
        b['ts']=pd.to_datetime(b.ts).dt.tz_convert('America/New_York')
        out.append(b[['symbol','ts','open','high','low','close','volume']])
    return pd.concat(out).set_index(['symbol','ts']).sort_index()
