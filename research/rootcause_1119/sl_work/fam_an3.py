import pandas as pd, numpy as np
exec(open('fam_an2.py').read().split("sh=x[x.side=='short']")[0])
B=pd.read_csv('remedyB_per_setup.csv',index_col=0)
def stats(d,w):
    rr=d.r*w; day=rr.groupby(d.date).sum(); ws=w.groupby(d.date).sum(); mu=rr.sum()/w.sum()
    se=np.sqrt(((day-ws*mu)**2).sum())/w.sum(); return mu/se, mu, day.min()/ws.mean()
rows=[]
for n in B.index:
    d=x[x.setup==n]; u14,u5=B.loc[n,'rsi14'],B.loc[n,'rsi5']
    gx=((d.tod==1045)&u14)|((d.tod==1000)&u5)
    k=d.groupby(['date','tod']).r.transform('size').astype(float)
    w=pd.Series(np.where(gx,1/np.sqrt(k),1.0),index=d.index)
    if not gx.any(): continue
    t0,m0,w0=stats(d,pd.Series(1.0,index=d.index)); t1,m1,w1=stats(d,w)
    rows.append({'setup':n,'t0':t0,'t1':t1,'avgR0':m0,'avgR1':m1,'worst0':w0,'worst1':w1})
R=pd.DataFrame(rows).set_index('setup'); R['dt']=R.t1-R.t0
print('gap-exit-bar burst weighting, rsi setups affected',len(R),'t up',(R.dt>0).sum(),'down',(R.dt<0).sum(),'median dt',R.dt.median().round(3),'worst-day better',(R.worst1>R.worst0).sum())
print(R.sort_values('dt').round(3).to_string())
