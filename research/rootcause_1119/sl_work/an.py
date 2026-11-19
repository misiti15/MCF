import pandas as pd, numpy as np, sys
sys.path.insert(0,'.'); sys.path.insert(0,'/home/user/MCF')
from classify import classes
from mcf.strategies.setups import refire_select
C,N=classes()
x=pd.read_parquet('lab_fires.parquet'); x['cls']=x.symbol.map(lambda s:C.get(s,'?'))
x['date']=pd.to_datetime(x.date).dt.date
x['per']=np.where(x.date.astype(str)<'2026-03-10','A_unseen(<03-10)','B_insample(>=03-10)')
def summ(g):
    d=g.groupby('date').r.sum(); tot=g.r.sum()
    if not len(g): return pd.Series(dtype=float)
    bd=d.idxmax(); nb=(g.date==bd).sum()
    se=np.sqrt(((d-g.groupby('date').size()*g.r.mean())**2).sum())/len(g) if len(d)>1 else np.nan
    return pd.Series({'n':len(g),'days':len(d),'win':(g.r>0).mean(),'avgR':g.r.mean(),'t':g.r.mean()/se if se else np.nan,'totR':tot,
                      'avgR_wo_best':(tot-d.max())/max(1,len(g)-nb),'best_share':d.max()/tot if tot>0 else np.nan})
pd.set_option('display.width',250)
f=x[x['first']]
for s in ['L3','ST7']:
    print('\n=== ',s,'first per symbol-day, by class'); print(f[f.setup==s].groupby('cls').apply(summ,include_groups=False).round(3).to_string())
    print(f[f.setup==s].groupby(['per','cls']).apply(summ,include_groups=False).round(3).to_string())
# refire chain approx (cooldown 1 on 5-min bars, max 3 per symbol-day)
rows=[]
for (s,sym,d),g in x[x.setup=='L3'].groupby(['setup','symbol','date']):
    bars=((g.tod//100)*60+g.tod%100)//5
    sel=refire_select(list(bars.values),1)
    keep=g[bars.isin(sel).values].head(3)
    rows.append(keep)
rf=pd.concat(rows)
print('\n=== L3 refire chain (cooldown 1, <=3 per symbol-day) by class'); print(rf.groupby('cls').apply(summ,include_groups=False).round(3).to_string())
rf.to_parquet('l3_refire.parquet')
