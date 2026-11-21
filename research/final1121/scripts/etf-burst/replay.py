"""Live replay of the 21 grid configs on live NM-ETF-family journal trades (LR8 cost-R), per account/setup, burst bars K>=4.
No latch re-simulation (lots blocked by the -2R latch after a burst are not added back). Educational only - not financial advice."""
from grid import cond, K
import pandas as pd, numpy as np
e=pd.read_parquet('live_etf.parquet'); e['em']=(e.tod//100)*60+e.tod%100
e=e.sort_values(['account','strategy','date','em','symbol']).reset_index(drop=True)
CF=[(c,a) for c in ['C0','C1','C2','C3','C4'] for a in ['A1','A2','A3']]+[(c,a) for c in ['V25','V30','V35'] for a in ['A1','A3']]
key=['account','strategy','date','tod']
nb=e.groupby(key).symbol.transform('size').to_numpy()
rows=[]
for c,a in CF:
    hit=(nb>=K)&np.asarray(cond(e,c),bool)
    keep=np.ones(len(e),bool)
    if a=='A1': rk=e.groupby(key+['grp']).cumcount().to_numpy(); keep[hit&(rk>=1)]=False
    if a=='A2': rk=e.groupby(key).cumcount().to_numpy(); keep[hit&(rk>=3)]=False
    if a=='A3': keep[hit]=False
    e['keep']=keep
    for (acct,st),g in e.groupby(['account','strategy']):
        d0=g.groupby('date').r.sum(); d1=g[g.keep].groupby('date').r.sum().reindex(d0.index,fill_value=0)
        dd=d1-d0; ch=dd[dd.abs()>1e-9]; w=g.date>='2026-11-17'
        rows.append(dict(cfg=c+a,acct=acct,setup=st,base=d0.sum(),new=d1.sum(),dR=dd.sum(),dR_1117_1120=dd[dd.index>='2026-11-17'].sum(),
                         better=int((ch>0).sum()),worse=int((ch<0).sum()),cut=int((~g.keep).sum()),changed=';'.join(f'{k}:{v:+.2f}' for k,v in ch.items())))
R=pd.DataFrame(rows); pd.set_option('display.width',250); pd.set_option('display.max_colwidth',60)
print(R.round(2).to_string(index=False))
R.to_csv('replay.csv',index=False)
print(R.groupby('cfg')[['dR','dR_1117_1120','better','worse','cut']].sum().round(2))
