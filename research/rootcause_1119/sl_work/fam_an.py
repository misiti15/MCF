import pandas as pd, numpy as np, sys, glob, yaml, re
sys.path.insert(0,'.')
from classify import classes
C,_=classes()
x=pd.read_parquet('family_trades.parquet'); x['cls']=x.symbol.map(lambda s:C.get(s,'stock'))
x['date']=pd.to_datetime(x.date).dt.date
mods={}
for p in sorted(glob.glob('/home/user/MCF/config/*.yaml')):
    try: y=yaml.safe_load(open(p))
    except Exception: continue
    for n,s in ((y or {}).get('strategies') or {}).items():
        if isinstance(s,dict) and s.get('type')=='lab' and s.get('enabled') and n not in mods: mods[n]=s['module']
src={n:open('/home/user/MCF/'+m).read() for n,m in mods.items()}
def uses(n,k):
    t=src.get(n,'')
    body=t.split('def mask',1)[-1]
    if k=='rsi': return bool(re.search(r"""['"]rsi['"]""",body)) or "'rsi14'" in t or 'rsi50' in t
    return bool(re.search(r"""['"]rsi5['"]""",body))
pd.set_option('display.width',250)
print('setups',x.setup.nunique(),'trades',len(x))
# ---- Remedy A: exclude market-inverse products (inverse ETFs, long-VIX)
g=x.groupby('setup')
A=pd.DataFrame({'n':g.size(),'R':g.r.sum(),'n_inv':g.apply(lambda d:(d.cls=='inv').sum()),'R_inv':g.apply(lambda d:d.r[d.cls=='inv'].sum())})
A['delta']=-A.R_inv
A['side']=g.side.first()
aff=A[A.n_inv>0]
print('\nRemedy A (no inverse products): affected',len(aff),'of',len(A),'improve',(aff.delta>0).sum(),'worse',(aff.delta<0).sum(),
      'sum delta',aff.delta.sum().round(1),'| improve sum',aff.delta[aff.delta>0].sum().round(1),'worse sum',aff.delta[aff.delta<0].sum().round(1))
print(aff.groupby('side').agg(k=('delta','size'),imp=('delta',lambda d:(d>0).sum()),wor=('delta',lambda d:(d<0).sum()),sum=('delta','sum')).round(1))
print('largest worse:',aff.sort_values('delta').head(6)[['n_inv','R_inv','delta']].round(2).to_string())
print('largest improve:',aff.sort_values('delta').tail(6)[['n_inv','R_inv','delta']].round(2).to_string())
inv=x[x.cls=='inv']; print('inverse trades pooled: n',len(inv),'avgR',inv.r.mean().round(3),'| short side',inv[inv.side=='short'].r.mean().round(3),len(inv[inv.side=='short']),'| long side',inv[inv.side=='long'].r.mean().round(3),len(inv[inv.side=='long']))
# split halves
for per,sub in [('unseen<03-10',x[x.date.astype(str)<'2026-03-10']),('>=03-10',x[x.date.astype(str)>='2026-03-10'])]:
    gg=sub[sub.cls=='inv'].groupby('setup').r.sum(); print(per,'setups w/ inv',len(gg),'improve',(gg<0).sum(),'worse',(gg>0).sum(),'sum delta',(-gg.sum()).round(1))
A.to_csv('remedyA_per_setup.csv')
# ---- Remedy B: skip the RSI gap-exit bar (RSI14: 10:45 bar; RSI5: 10:00 bar) for setups whose mask reads that RSI
rows=[]
for n,d in x.groupby('setup'):
    u14,u5=uses(n,'rsi'),uses(n,'rsi5')
    if not (u14 or u5): continue
    drop=((d.tod==1045)&u14)|((d.tod==1000)&u5)
    rows.append({'setup':n,'rsi14':u14,'rsi5':u5,'n':len(d),'R':d.r.sum(),'n_drop':int(drop.sum()),'R_drop':d.r[drop].sum(),'avg_drop':d.r[drop].mean() if drop.any() else np.nan,'avg_keep':d.r[~drop].mean()})
B=pd.DataFrame(rows).set_index('setup'); B['delta']=-B.R_drop
bf=B[B.n_drop>0]
print('\nRemedy B (skip RSI gap-exit bar): rsi setups',len(B),'affected',len(bf),'improve',(bf.delta>0).sum(),'worse',(bf.delta<0).sum(),'sum',bf.delta.sum().round(1),'| imp',bf.delta[bf.delta>0].sum().round(1),'wor',bf.delta[bf.delta<0].sum().round(1))
print(bf.sort_values('delta')[['rsi14','rsi5','n','n_drop','avg_drop','avg_keep','delta']].round(3).to_string())
B.to_csv('remedyB_per_setup.csv')
# fire concentration at gap-exit bar: rsi14 setups
# ---- Remedy A' : exclude inverse products from SHORT setups only (short inverse = market long)
sh=x[x.side=='short']; gi=sh[sh.cls=='inv'].groupby('setup').r.agg(['size','mean','sum'])
print("\nRemedy A' (short setups only): short setups",sh.setup.nunique(),'affected',len(gi),'improve',(gi['sum']<0).sum(),'worse',(gi['sum']>0).sum(),'net',(-gi['sum'].sum()).round(1),'imp',(-gi['sum'][gi['sum']<0].sum()).round(1),'wor',(-gi['sum'][gi['sum']>0].sum()).round(1))
for per,sub in [('unseen<03-10',sh[sh.date.astype(str)<'2026-03-10']),('>=03-10',sh[sh.date.astype(str)>='2026-03-10'])]:
    gg=sub[sub.cls=='inv'].groupby('setup').r.sum(); print(' ',per,'affected',len(gg),'improve',(gg<0).sum(),'worse',(gg>0).sum(),'net',(-gg.sum()).round(1))
print(gi.sort_values('sum').round(3).to_string())
si=sh[sh.cls=='inv']; d=si.groupby('date').r.sum()
print('pooled short-inverse lab: n',len(si),'avgR',si.r.mean().round(3),'win',(si.r>0).mean().round(3),'days',len(d),'sum',si.r.sum().round(1),'w/o best day',(si.r.sum()-d.max()).round(1))
li=x[(x.side=='long')&(x.cls=='inv')]; print('pooled long-inverse lab: n',len(li),'avgR',li.r.mean().round(3))
