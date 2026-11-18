"""W4 pooled view: setup-relative condition terciles and fixed time buckets, fit vs check halves. Educational only."""
import pandas as pd, numpy as np
exec(open('code/analyze.py').read().split("mapping=[]")[0])
B=pd.read_csv('baseline.csv'); print('total excess vs random',round(B.excess.sum(),1),'mean',round(B.excess.mean(),2))
rows=[]
for s in setups:
    d=x[(x.strategy==s)&(~x.dup)].dropna(subset=['tod']).copy()
    days=sorted(d.date.unique()); half=set(days[:len(days)//2]); d['half']=np.where(d.date.isin(half),'fit','check')
    for c in COND:
        v=d[c]; 
        if v.notna().sum()<30: continue
        d[c+'_t']=pd.qcut(v.rank(method='first'),3,labels=['low','mid','high'])
    d['todb']=pd.cut(d.tod,[0,30,60,120,240,330,999],right=False,labels=['0930','1000','1030','1130','1330','1500'])
    rows.append(d)
P=pd.concat(rows)
out=[]
for c in COND+['todb']:
    col=c if c=='todb' else c+'_t'
    g=P.groupby([col,'half'],observed=True).R.agg(['size','mean']).unstack('half')
    g.columns=[f'{a}_{b}' for a,b in g.columns]; g['cond']=c; out.append(g.reset_index().rename(columns={col:'bucket'}))
O=pd.concat(out)[['cond','bucket','size_fit','mean_fit','size_check','mean_check']]
O.to_csv('pooled.csv',index=False); print(O.round(3).to_string())
# per setup: is the 09:30-10:00 bucket worse than the rest in both halves?
r=[]
for s,d in P.groupby('strategy'):
    for h in ('fit','check'):
        a=d[(d.half==h)&(d.todb=='0930')].R; b=d[(d.half==h)&(d.todb!='0930')].R
        r.append(dict(setup=s,half=h,n_open=len(a),open=a.mean(),rest=b.mean()))
T=pd.DataFrame(r).pivot(index='setup',columns='half',values=['n_open','open','rest'])
T=T[(T[('n_open','fit')]>=10)&(T[('n_open','check')]>=10)]
w=((T[('open','fit')]<T[('rest','fit')])&(T[('open','check')]<T[('rest','check')])).sum()
print('setups with >=10 open-bucket trades each half:',len(T),'open worse in both:',w, 'better in both:',((T[('open','fit')]>T[('rest','fit')])&(T[('open','check')]>T[('rest','check')])).sum())
