import pandas as pd, numpy as np, sys, glob
sys.path.insert(0,'.'); sys.path.insert(0,'/home/user/MCF/research/history2y')
from classify import classes
from lib import load_context, months
C,N=classes()
ctx=pd.concat([load_context(m) for m in months()])
ctx['date']=pd.to_datetime(ctx.date).dt.date
from lib import daily
dd=daily(); dd=dd[dd.symbol=='SPY']; spyc=pd.Series(((dd.close/dd.open-1)*100).values,index=dd.date.values)
x=pd.read_parquet('lab_fires.parquet'); x['cls']=x.symbol.map(lambda s:C.get(s,'?')); x['date']=pd.to_datetime(x.date).dt.date
x=x.merge(ctx[['date','tod','spy_fo','qqq_fo']],on=['date','tod'],how='left')
x['spy_rest']=(1+x.date.map(spyc)/100)/(1+x.spy_fo/100)*100-100
x['spy_oc']=x.date.map(spyc)
x.to_parquet('lab_fires_ctx.parquet')
f=x[x['first']].copy()
pd.set_option('display.width',250)
def summ(g):
    d=g.groupby('date').r.sum(); tot=g.r.sum()
    se=np.sqrt(((d-g.groupby('date').size()*g.r.mean())**2).sum())/len(g) if len(d)>1 else np.nan
    return pd.Series({'n':len(g),'days':len(d),'win':(g.r>0).mean(),'avgR':g.r.mean(),'t':g.r.mean()/se if se else np.nan,'totR':tot})
# ---- ST7 clusters
s=f[f.setup=='ST7'].copy()
s['clu5']=s.groupby(['date','tod']).r.transform('size')
s['clu15']=s.groupby(['date',s.tod//15*0+((s.tod//100)*60+s.tod%100)//15]).r.transform('size')
s['day_n']=s.groupby('date').r.transform('size')
for col in ['clu5','clu15','day_n']:
    s['b']=pd.cut(s[col],[0,1,2,4,6,1000],labels=['1','2','3-4','5-6','7+'])
    print('\nST7 by',col); print(s.groupby('b',observed=True).apply(summ,include_groups=False).round(3).to_string())
# agreement within 5-min clusters size>=3
g=s[s.clu5>=3].groupby(['date','tod']).r
agree=g.apply(lambda r:((r>0).all() or (r<=0).all())).mean()
p=(s.r>0).mean()
sz=s[s.clu5>=3].groupby(['date','tod']).size()
exp_agree=np.mean([p**k+(1-p)**k for k in sz])
print('\nST7 clusters>=3 :',len(sz),'all-same-outcome share',round(agree,3),'expected if independent',round(exp_agree,3))
# beta to SPY rest-of-day
for nm,gg in [('ST7',s),('L3-inv',f[(f.setup=='L3')&(f.cls=='inv')]),('L3-stock',f[(f.setup=='L3')&(f.cls=='stock')]),('L3-lev',f[(f.setup=='L3')&(f.cls=='lev')])]:
    gg=gg.dropna(subset=['spy_rest'])
    b=np.polyfit(gg.spy_rest,gg.r,1)
    print(nm,'n',len(gg),'corr(R, SPY entry->15:55 %)',round(np.corrcoef(gg.spy_rest,gg.r)[0,1],3),'slope R per 1% SPY',round(b[0],3))
# ST7 by SPY rest-of-day bucket
s['spyb']=pd.cut(s.spy_rest,[-9,-0.5,-0.15,0.15,0.5,9])
print('\nST7 by SPY entry->15:55 move'); print(s.groupby('spyb',observed=True).apply(summ,include_groups=False).round(3).to_string())
L=f[(f.setup=='L3')].copy(); L['spyb']=pd.cut(L.spy_rest,[-9,-0.5,-0.15,0.15,0.5,9])
print('\nL3 by class x SPY entry->15:55'); print(L.groupby(['cls','spyb'],observed=True).apply(summ,include_groups=False).round(3).to_string())
# L3 inverse: what was the market doing at entry? spy_fo at entry
I=L[L.cls=='inv']
print('\nL3 inverse entries: SPY from open at entry: median',I.spy_fo.median().round(2),' share SPY<0 at entry',(I.spy_fo<0).mean().round(3))
print('L3 stock entries: SPY from open at entry: median',L[L.cls=='stock'].spy_fo.median().round(2),' share SPY<0',(L[L.cls=='stock'].spy_fo<0).mean().round(3))
print('L3 inv symbols top:',I.symbol.value_counts().head(12).to_dict())
