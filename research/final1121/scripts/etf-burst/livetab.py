import pandas as pd, numpy as np
from base import INV, GROUP
L=pd.read_parquet('live_all.parquet')
e=L[L.strategy.str.contains('NM-ETF')|L.strategy.str.contains('etf-long')].copy()
st=pd.to_datetime(e.signal_time.fillna(e.entry_time),utc=True,format='mixed').dt.tz_convert('America/New_York')
m=st.dt.hour*60+st.dt.minute; m=(m//5)*5; e['tod']=(m//60)*100+m%60
e['inv']=e.symbol.isin(INV); e['grp']=e.symbol.map(GROUP).fillna(e.symbol)
F=pd.read_parquet('idx_feats_live.parquet'); D=pd.read_parquet('spy_daily_live.parquet')
e=e.merge(F,on=['date','tod'],how='left').merge(D,left_on='date',right_index=True,how='left')
e.to_parquet('live_etf.parquet')
e['nbar']=e.groupby(['account','strategy','date','tod']).r.transform('size')
e['d']=np.where(e.inv,-1,1)
g=e[e.nbar>=3].groupby(['account','strategy','date','tod']).agg(n=('r','size'),d=('d','mean'),R=('r','sum'),fo=('spy_fo','first'),vw=('spy_vw','first'),s13=('spy_s1300','first'),pos=('spy_pos','first'),r15=('spy_r15','first'),atr=('atr14p','first'))
g['r15n']=g.r15/g.atr
pd.set_option('display.width',250); print(g.round(2).to_string())
print(e.groupby(['strategy','account']).agg(n=('r','size'),R=('r','sum'),d0=('date','min')))
