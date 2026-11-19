# Counterfactual bracket anchoring on live fills, 1-min walk from the minute AFTER the fill minute (stop checked first).
import sys, pandas as pd, numpy as np
sys.argv=[sys.argv[0], sys.argv[1]] if len(sys.argv)>1 else sys.argv
W='exec_data'
exec(open('exec_scripts/audit.py').read().split("def load(")[0].replace("W = sys.argv[1]","W = 'exec_data'"))
A=pd.read_csv(f'{W}/audit_trades.csv')
A=A[A.ent_slip_R.abs()<=2]
ET="America/New_York"
def walk(b, sd, entry, stop, target):
    for _, x in b.iterrows():
        if (x.low<=stop) if sd>0 else (x.high>=stop): return sd*(stop-entry), 'stop'
        if (x.high>=target) if sd>0 else (x.low<=target): return sd*(target-entry), 'target'
    return sd*(b.close.iloc[-1]-entry), 'flat'
res=[]
import sqlite3
for _, t in A.iterrows():
    b=bars(t.symbol, t.date)
    if b is None: continue
    em=pd.Timestamp(f"{t.date} {t.entry_et}", tz=ET).floor('min')
    p=b[(b.index>em)&(b.index<=em.normalize()+pd.Timedelta(hours=15,minutes=55))]
    if len(p)==0: continue
    sd=t.side; rf=abs(t.ref-t.stop); rfill=abs(t.entry-t.stop)
    g0,k0=walk(p,sd,t.entry,t.stop,t.target)                       # actual bracket
    g1,k1=walk(p,sd,t.entry,t.stop,t.entry+sd*rfill)               # target re-anchored to fill (1R of fill risk)
    g2,k2=walk(p,sd,t.entry,t.entry-sd*rf,t.entry+sd*rf)           # whole bracket re-centred on fill
    res.append(dict(setup=t.strategy[:3],acct=t.acct,date=t.date,symbol=t.symbol,itype=t.itype,R=t.R,slip=t.ent_slip_R,
        sim0=g0/rfill,k0=k0,sim1=g1/rfill,k1=k1,sim2=g2/rf,k2=k2,actual_reason=t.reason))
R=pd.DataFrame(res); R.to_csv(f'{W}/anchor.csv',index=False)
R['cost']=R.R-R.sim0  # implied cost+exit slip vs gross sim, applied to all variants (approx)
for v in ['sim0','sim1','sim2']: R[v+'_net']=R[v]+R.cost.clip(-0.5,0.5)
print('parity: actual vs sim0 reason match', (R.k0.str[:4]==R.actual_reason.str[:4]).mean().round(3), len(R))
print(R.groupby('setup')[['R','sim0','sim1','sim2']].agg(['mean','sum']).round(3))
print(R[R.date=='2026-11-19'][['setup','symbol','R','slip','sim0','k0','sim1','k1','sim2','k2']].round(2).to_string())
for v in ['sim1','sim2']:
    d=R[v]-R.sim0
    print(v,'trades better',(d>0.01).sum(),'worse',(d<-0.01).sum(),'sum',d.sum().round(2))
    print(R.assign(d=d).groupby(['setup']).d.agg(['count','sum','mean']).round(3))
    print(R.assign(d=d).groupby(['setup','acct']).d.agg(['count','sum','mean']).round(3))
    dd=R.assign(d=d).groupby(['setup','date']).d.sum(); print('days better/worse',(dd>0).sum(),(dd<0).sum(), 'best day share', (dd.max()/d.sum()).round(2) if d.sum()>0 else None)
