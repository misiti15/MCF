# Stop-width counterfactual on live fills (1-min walk after fill minute, stop first, target unchanged, flat 15:55).
# R_k = gross points / (k * fill risk) -> same $ risk; a size-only control = sim(k=1)/k.
import pandas as pd, numpy as np
exec(open('exec_scripts/audit.py').read().split("def load(")[0].replace("W = sys.argv[1]","W = 'exec_data'"))
A=pd.read_csv('exec_data/audit_trades.csv'); A=A[~A.strategy.str.startswith('RW3')]
ET="America/New_York"
def walk(b, sd, entry, stop, target):
    lo=b.low.values; hi=b.high.values
    for i in range(len(b)):
        if (lo[i]<=stop) if sd>0 else (hi[i]>=stop): return sd*(stop-entry)
        if (hi[i]>=target) if sd>0 else (lo[i]<=target): return sd*(target-entry)
    return sd*(b.close.values[-1]-entry)
rows=[]
for _,t in A.iterrows():
    b=bars(t.symbol,t.date)
    if b is None: continue
    em=pd.Timestamp(f"{t.date} {t.entry_et}",tz=ET).floor('min')
    p=b[(b.index>em)&(b.index<=em.normalize()+pd.Timedelta(hours=15,minutes=55))]
    if not len(p): continue
    sd=t.side; r=abs(t.entry-t.stop); d=dict(setup=t.strategy[:3],itype=t.itype,date=t.date,acct=t.acct,R=t.R)
    for k in (0.75,1.0,1.25,1.5,2.0):
        d[f'k{k}']=walk(p,sd,t.entry,t.entry-sd*k*r,t.target)/(k*r)
    rows.append(d)
X=pd.DataFrame(rows); X.to_csv('exec_data/width.csv',index=False)
X['ctl15']=X['k1.0']/1.5
for k in (0.75,1.25,1.5,2.0):
    X[f'd{k}']=X[f'k{k}']-X['k1.0']
print(X.groupby(['setup','itype'])[['k1.0','k0.75','k1.25','k1.5','k2.0','ctl15']].mean().round(3).assign(n=X.groupby(['setup','itype']).size()))
print(X.groupby('setup')[['k1.0','k0.75','k1.25','k1.5','k2.0','ctl15']].mean().round(3))
# stop effect vs size control at k=1.5
X['eff15']=X['k1.5']-X['ctl15']
print(X.groupby(['setup','itype']).eff15.agg(['count','mean','sum']).round(3))
