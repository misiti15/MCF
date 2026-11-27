import pandas as pd, numpy as np
t=pd.read_csv('live_all.csv.gz'); t=t[~t.dup]
P=t[t.account=='primary'].groupby('date').r.sum()
s=t[t.strategy=='NM-AR-AM-gapdown-capitulation-long'].copy()
et=pd.to_datetime(s.entry_time,utc=True); xt=pd.to_datetime(s.exit_time,utc=True)
s['hold']=(xt-et).dt.total_seconds()/60
d=s.groupby('date').r.sum()
print('first/last',s.date.min(),s.date.max(),'sessions traded',d.size)
print('median hold',s.hold.median())
# breakeven win: avg win R and avg loss R
w=s[s.r>0].r.mean(); l=-s[s.r<=0].r.mean(); print('win%',(s.r>0).mean(),'BE win%',l/(w+l), 'avgwin',w,'avgloss',l)
def ct(x):
    m=x.r.mean(); e=(x.r-m).groupby(x.date).sum(); return m/(np.sqrt((e**2).sum())/len(x))
print('clustered t',ct(s))
# correlation with primary live over primary sessions
days=P.index
dd=d.reindex(days).fillna(0)
print('corr w/ Primary daily R',np.corrcoef(dd,P)[0,1], 'n days',len(days))
worst=P.nsmallest(10); print('Primary 10 worst', worst.round(1).to_dict())
print('seed R on those days',dd[worst.index].round(2).to_dict(), dd[worst.index].sum())
for a,b in [('2026-10-01','2026-11-01'),('2026-11-02','2026-11-30')]:
    x=s[(s.date>=a)&(s.date<=b)]; print(a,b,len(x),x.r.mean())
print('excl 11-24', s[s.date!='2026-11-24'].r.mean(), 'excl 10-22', s[s.date!='2026-10-22'].r.mean())
print(s.r.describe())
