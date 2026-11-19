"""EXIT100 base-rate check (W1-redteam). Run `python jl.py` first (writes all.pkl). Flag on sessions 1-23, score the last 8
(11-06..11-17). Educational only - not financial advice."""
import pandas as pd,numpy as np
a=pd.read_pickle('all.pkl'); a=a[(a.date<='2026-11-17')&a.R.notna()&np.isfinite(a.R)]
post_cost=(a[a.date>='2026-11-12'].cost).mean(); a['Runi']=a.Rraw-post_cost
days=sorted(a.date.unique())
for accs,lab in [(['ondeck','testA','testB','testC','testD','testE','testF','gen'],'arena'),(['ondeck','testA','testB','testC','testD','testE','testF','gen','graveyard'],'arena+GY')]:
  ar=a[a.acct.isin(accs)].copy(); ar['key']=ar.strategy
  for col in ['R','Rraw','Runi']:
    for minad in [10,15]:
      fitd=days[:-8]; f=ar[ar.date.isin(fitd)]; c=ar[~ar.date.isin(fitd)]
      g=f.groupby(['key','date'])[col].sum()
      st=f.groupby('key').agg(n=(col,'size'),avg=(col,'mean'),ad=('date','nunique'),tot=(col,'sum'))
      bestd=g.groupby(level=0).idxmax().map(lambda t:t[1])
      st['wob']=[st.tot[k]-g[(k,bestd[k])] for k in st.index]
      big=st[(st.n>=100)&(st.ad>=minad)]
      flag=big[(big.avg<=-0.05)&(big.wob<=0)].index; other=big[~big.index.isin(flag)].index
      fl=c[c.key.isin(flag)]; ot=c[c.key.isin(other)]
      rec=(c[c.key.isin(flag)].groupby('key')[col].mean()>0).sum()
      print(lab,col,'minad',minad,'flag',len(flag),'later',len(fl),round(fl[col].mean(),3),round(fl[col].sum(),1),'recovered',rec,'| other100+',len(other),len(ot),round(ot[col].mean(),3),'| all later',round(c[col].mean(),3))
