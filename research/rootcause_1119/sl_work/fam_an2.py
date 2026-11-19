import pandas as pd, numpy as np, sys, glob, yaml, re
sys.path.insert(0,'.')
from classify import classes
C,_=classes()
x=pd.read_parquet('family_trades.parquet'); x['cls']=x.symbol.map(lambda s:C.get(s,'stock')); x['date']=pd.to_datetime(x.date).dt.date
mods={}
for p in sorted(glob.glob('/home/user/MCF/config/*.yaml')):
    try: y=yaml.safe_load(open(p))
    except Exception: continue
    for n,s in ((y or {}).get('strategies') or {}).items():
        if isinstance(s,dict) and s.get('type')=='lab' and s.get('enabled') and n not in mods: mods[n]=s['module']
def reads_gap(n):
    t=open('/home/user/MCF/'+mods[n]).read().split('def mask',1)[-1]
    return bool(re.search(r"""['"]gap['"]""",t)) or 'gap_' in t.lower() or 'Gaple' in n or 'Gapge' in n
sh=x[x.side=='short']
fam=[n for n in sh.setup.unique() if reads_gap(n)]
print('gap-reading short setups:',len(fam))
for lbl,sub in [('all',sh),('unseen<03-10',sh[sh.date.astype(str)<'2026-03-10']),('>=03-10',sh[sh.date.astype(str)>='2026-03-10'])]:
    s=sub[sub.setup.isin(fam)]; gi=s[s.cls=='inv'].groupby('setup').r.sum()
    print(lbl,'affected',len(gi),'improve',(gi<0).sum(),'worse',(gi>0).sum(),'net',(-gi.sum()).round(1),'imp',(-gi[gi<0].sum()).round(1),'wor',(-gi[gi>0].sum()).round(1))
s=sh[sh.setup.isin(fam)]; gi=s[s.cls=='inv'].groupby('setup').r.agg(['size','mean','sum'])
print(gi.sort_values('sum').round(3).to_string())
nf=sh[~sh.setup.isin(fam)]; gn=nf[nf.cls=='inv'].groupby('setup').r.sum(); print('non-gap short setups: affected',len(gn),'improve',(gn<0).sum(),'worse',(gn>0).sum(),'net',(-gn.sum()).round(1))
# gap-reading LONG setups on inverse (gap-up thesis flips too)
lo=x[x.side=='long']; famL=[n for n in lo.setup.unique() if reads_gap(n)]
gl=lo[lo.setup.isin(famL)&(lo.cls=='inv')].groupby('setup').r.sum(); print('gap-reading long setups',len(famL),'affected',len(gl),'improve',(gl<0).sum(),'worse',(gl>0).sum(),'net',(-gl.sum()).round(1))
pd.Series(fam).to_csv('gap_short_family.csv',index=False)
# ---- burst weighting test: same-setup same-bar fires k -> weight 1/sqrt(k); report day-t and worst day per setup
def stats(d,w):
    rr=d.r*w; day=rr.groupby(d.date).sum(); wsum=w.groupby(d.date).sum()
    mu=rr.sum()/w.sum(); se=np.sqrt(((day-wsum*mu)**2).sum())/w.sum()
    return mu/se, day.min()/w.groupby(d.date).sum().mean()
rows=[]
for n,d in x.groupby('setup'):
    k=d.groupby(['date','tod']).r.transform('size').astype(float)
    if (k>=3).sum()<20: continue
    t0,w0=stats(d,pd.Series(1.0,index=d.index)); t1,w1=stats(d,1/np.sqrt(k))
    rows.append({'setup':n,'n':len(d),'share_k3':(k>=3).mean(),'t_base':t0,'t_burst':t1,'worst_base(per avg day risk)':w0,'worst_burst':w1})
B=pd.DataFrame(rows).set_index('setup'); B['dt']=B.t_burst-B.t_base
print('\nburst 1/sqrt(k) weighting: setups with >=20 trades in 3+ bursts',len(B),'day-t up',(B.dt>0).sum(),'down',(B.dt<0).sum(),'median dt',B.dt.median().round(2))
print(B.loc[[i for i in ['ST7-rsi50dn-long-pm-t1s1-FD','ST7Q-rsi50dn-qqqbelowvwap-long-t1s1-FD','L3-gap-slope-fromopen-FD'] if i in B.index]].round(3).to_string())
B.to_csv('burst_weight_per_setup.csv')
