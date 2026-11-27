import sys, numpy as np, pandas as pd
sys.path.insert(0,sys.argv[1]+'/research/ultimate_1119/top10'); sys.path.insert(0,sys.argv[1])
import bench10 as B
sys.path.insert(0,'.')
from caplib import GRID
P='/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/pyramid'
etb=pd.read_parquet(P+'/S/etb_rate.parquet').rate
def period(d):
    if ("2024-10-01" <= d <= "2024-10-31") or ("2025-03-01" <= d <= "2025-09-30"): return "FIT"
    if d >= "2025-10-01": return "CHECK"
    if "2023-01-03" <= d <= "2024-09-13": return "T2"
    return "none"
parts=[]
for f in ['fit','check','t2']:
    x=pd.read_parquet(f'{P}/L1/trades_{f}.parquet'); x=x[x.kind_=='prim'].rename(columns={'cfg':'setup'}); parts.append(x)
for f in ['t1','t2']:
    x=pd.read_parquet(f'{P}/S/work/trades_{f}.parquet'); x=x[~x.setup.str.endswith('|RND')&(x.setup!='L3-gap-slope-fromopen-FD')]; parts.append(x)
T=pd.concat(parts,ignore_index=True); T['date']=T.date.astype(str)
T=T[T.date.map(period)!='none']
assert not ((T.date>='2024-11-01')&(T.date<='2025-02-28')).any()
T=B.add_r(T)
home={'L3-gap-slope-fromopen-FD':'primary','RW3-gapdn-rsi5pop-flowsell-short-FD':'primary','RW5-heat30-flowsell-rsi5pop-gapdn-short-FD':'primary','NM-ETF-late-dip-di-long':'primary'}
rows=[]
for s,g in T.groupby('setup'):
    rules=dict(B.BOOK[home.get(s,'testingd')]); 
    base=None; per={}
    for L in [None]+GRID:
        rules['latch']=L; b=B.book(g,rules,etb)
        per[L]=b.groupby('date').agg(R=('r','sum'),n=('r','size'))
        if L is None: base=b
    pm=base.sort_values(['date','xm'],kind='mergesort').groupby('date').r.apply(lambda v:v.cumsum().min())
    D=per[None].rename(columns={'R':'Rnone','n':'nnone'})
    D['final']=D.Rnone; D['pmin']=pm
    for L in GRID: D[f'R{L}']=per[L].R.reindex(D.index).fillna(0); D[f'n{L}']=per[L].n.reindex(D.index).fillna(0)
    D=D.reset_index(); D['strategy']=s; D['per']=D.date.map(period); rows.append(D)
    print(s, len(base), round(base.r.sum(),1), {L:round(per[L].R.sum()-base.r.sum(),1) for L in [-1.0,-2.0,-3.0,-4.0]}, flush=True)
M=pd.concat(rows,ignore_index=True); M.to_parquet('lab_mat.parquet'); print(M.shape)
