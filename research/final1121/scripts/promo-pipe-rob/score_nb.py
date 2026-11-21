import sys; sys.argv=['x','w','none']
import pandas as pd, numpy as np, math
exec(open('nb.py').read().split('if __name__ == "__main__":')[0])
etb=pd.read_parquet('etb_rate.parquet').rate
T=add_r(pd.read_parquet('w/trades_t1.parquet')); T['half']=half(T.date)
def rec(x):
    if len(x)<3: return dict(n=len(x))
    d=x.groupby('date').r.sum(); s=d.sort_values(ascending=False); tot=x.r.sum()
    e=(x.r-x.r.mean()).groupby(x.date).sum(); G=e.size; se=math.sqrt((e**2).sum()*G/(G-1))/len(x)
    return dict(n=len(x),days=d.size,avg=round(x.r.mean(),3),wo1=round(x[x.date!=s.index[0]].r.mean(),3),
       wo2=round(x[~x.date.isin(s.index[:2])].r.mean(),3),bshare=round(s.iloc[0]/tot,2) if tot>0 else None,t=round(x.r.mean()/se,2),green=round((d>0).mean(),2))
rows=[]
for v in VARS:
    b=book(T[T.setup==v[0]],BOOK['testing'],etb)
    for h in ('fit','check'):
        rows.append(dict(cfg=v[0],part=h,**rec(b[b.half==h])))
    if v[0].endswith('base'):
        c=b[b.half=='check']; ds=sorted(c.date.unique()); m=ds[len(ds)//2]
        rows.append(dict(cfg=v[0],part='check-h1',**rec(c[c.date<m]))); rows.append(dict(cfg=v[0],part='check-h2',**rec(c[c.date>=m])))
        f=b[b.half=='fit']
        rows.append(dict(cfg=v[0],part='fit w/o Apr25',**rec(f[~f.date.str.startswith('2025-04')])))
        for mth,g in b[b.half!='none'].groupby(b.date.str[:7]): rows.append(dict(cfg=v[0],part='m '+mth,**rec(g)))
pd.set_option('display.width',250); pd.set_option('display.max_rows',200)
print(pd.DataFrame(rows).to_string(index=False)); print('T1 last date', T.date.max())
