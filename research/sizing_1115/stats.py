# Sizing-up study 2026-11-15 (run from the repo root). Educational only - not financial advice.
import sys,json;sys.path.insert(0,'research/sizing_1115')
import pandas as pd,numpy as np
from load import load
t=load()
A=json.load(open('docs/live/assignments.json'))['accounts']
T6=A['primary']; OD=A['testing']
def st(s,sub):
    g=sub.groupby('date').R.agg(['sum','size'])
    n=len(sub); ses=len(g); tot=g['sum'].sum()
    best=g['sum'].max(); bshare=best/tot if tot>0 else float('nan')
    wo=(tot-best)/(n-g.loc[g['sum'].idxmax(),'size']) if ses>1 else float('nan')
    wos=(tot-best)/(ses-1) if ses>1 else float('nan')
    return dict(setup=s,trades=n,sessions=ses,tps=n/ses,green=(g['sum']>0).mean()*100,avgR=tot/n,avgRses=tot/ses,
      worst=g['sum'].min(),std=g['sum'].std(),best=best,bshare=bshare*100,woR=wo,woRses=wos,tot=tot,
      pre=sub[sub.date<'2026-11-12'].R.mean(),post=sub[sub.date>='2026-11-12'].R.mean(),npost=(sub.date>='2026-11-12').sum(),
      prim_n=(sub.acct=='primary').sum(), accts=','.join(sorted(sub.acct.unique())))
rows=[]
for grp,L in (('T6',T6),('OD',OD)):
    for s in L:
        sub=t[t.strategy==s]
        if len(sub): r=st(s,sub); r['grp']=grp; rows.append(r)
df=pd.DataFrame(rows)
pd.set_option('display.width',250); pd.set_option('display.max_columns',30)
print(df.round(3).to_string())
df.to_csv('research/sizing_1115/stats.csv',index=False)
