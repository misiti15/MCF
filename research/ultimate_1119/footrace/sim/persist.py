import pandas as pd, numpy as np
d=pd.read_parquet('ev1119/w/trades.parquet')
rows=[]
for s,g in d.groupby('strategy'):
    days=sorted(g.date.unique())
    if len(days)<8 or len(g)<40: continue
    h=days[len(days)//2]; a=g[g.date<h]; b=g[g.date>=h]
    if len(a)<15 or len(b)<15: continue
    da=a.groupby('date').r_multiple.sum(); 
    # day-clustered t on first half (per-day mean R sums / trades)
    dm=a.groupby('date').r_multiple.mean(); t=dm.mean()/(dm.std(ddof=1)/np.sqrt(len(dm))) if len(dm)>2 and dm.std()>0 else 0
    best=da.idxmax(); wo=a[a.date!=best].r_multiple.mean()
    rows.append(dict(s=s,na=len(a),nb=len(b),aa=a.r_multiple.mean(),ab=b.r_multiple.mean(),wo=wo,t=t,ta=a.r_multiple.sum(),tb=b.r_multiple.sum()))
x=pd.DataFrame(rows); print(len(x),'setups with >=40 trades, >=8 days; split by session halves')
print('spearman avgR half1 vs half2: %.3f'%x.aa.corr(x.ab,method='spearman'))
print('sign kept: %.2f'%((np.sign(x.aa)==np.sign(x.ab)).mean()))
for name,m in [('avg<=0 & wo<=0',(x.aa<=0)&(x.wo<=0)),('avg<=-0.05 & wo<=0',(x.aa<=-0.05)&(x.wo<=0)),('avg<=-0.10 & wo<=0',(x.aa<=-0.10)&(x.wo<=0)),('clustered t<=-2 & wo<=0',(x.t<=-2)&(x.wo<=0)),('top quartile avg',x.aa>=x.aa.quantile(.75)),('all',x.aa==x.aa)]:
    y=x[m]; print(f"{name:26s} n={len(y):3d}  half2 avgR mean {y.ab.mean():+.3f} (trade-wtd {(y.ab*y.nb).sum()/y.nb.sum():+.3f})  half2>0: {(y.ab>0).mean():.2f}  half2 totR {y.tb.sum():+.1f}")
print('---')
for name,m in [('B: avg<=0 & wo<=0 & t<=-1.5',(x.aa<=0)&(x.wo<=0)&(x.t<=-1.5)),('A but t>-1.5',(x.aa<=0)&(x.wo<=0)&(x.t>-1.5)),('not A',~((x.aa<=0)&(x.wo<=0)))]:
    y=x[m]; print(f"{name:30s} n={len(y):3d} half2 avg {y.ab.mean():+.3f} trade-wtd {(y.ab*y.nb).sum()/y.nb.sum():+.3f} half2>0 {(y.ab>0).mean():.2f} tb {y.tb.sum():+.1f} nb {y.nb.sum()}")
