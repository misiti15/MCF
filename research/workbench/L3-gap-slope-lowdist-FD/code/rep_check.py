import pandas as pd, numpy as np, sys
import sim2, sim_low
def mk_path(df):
    mn = df.index.hour * 60 + df.index.minute
    return (np.asarray(mn), df.open.values, df.high.values, df.low.values, df.close.values)
RF = pd.read_parquet("replay_frames.parquet"); RF["tod"] = RF["tod"].astype(int); RF["date"] = RF.date.astype(str)
R1 = pd.read_parquet("replay_1min.parquet")
RP = {k: mk_path(g) for k, g in R1.groupby(["symbol", "date"])}
v=dict(sim_low.PARENT)
t=sim_low.book(sim_low.trades(RF,v,lambda s,d: RP.get((s,d))),v)
print(sim_low.stats(t))
v2=dict(v,costf=None); t2=sim_low.book(sim_low.trades(RF,v2,lambda s,d: RP.get((s,d))),v2); print('nocostf',sim_low.stats(t2))
s=pd.read_parquet('signals.parquet'); s=s[~s.reason.fillna('').str.contains('shortable')]
s['tod']=pd.to_datetime(s.ts,utc=True).dt.tz_convert('America/New_York'); s['tod']=s.tod.dt.hour*100+s.tod.dt.minute//5*5
m=s.merge(t2[['symbol','date','tod']].rename(columns={'date':'day'}),on=['symbol','day'],how='outer',suffixes=('_live','_bt'),indicator=True)
print(m._merge.value_counts()); b=m[m._merge=='both']; print('same bar', (b.tod_live==b.tod_bt).mean(), 'diff in 5min', ((b.tod_live-b.tod_bt).abs()<=5).mean())
print(b[b.tod_live!=b.tod_bt][['symbol','day','tod_live','tod_bt']].head(10))
print(m[m._merge=='left_only'][['symbol','day','tod_live','reason']].head(10))
