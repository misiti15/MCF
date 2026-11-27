import pandas as pd, numpy as np, sys
sys.path.insert(0,'.')
from caplib import *
V=sys.argv[1] if len(sys.argv)>1 else ''
t=pd.read_parquet(f'all_trades{V}.parquet'); t=t[t.date<='2026-11-24']
S=[l.strip() for l in open('setups.csv')]
t=t[t.strategy.isin(S)].copy()
t['et']=pd.to_datetime(t.entry_time,utc=True,format='mixed'); t['xt']=pd.to_datetime(t.exit_time,utc=True,format='mixed')
t['e']=t.et.astype('int64')//10**9; t['x']=t.xt.astype('int64')//10**9
def latched_acct(a,d):
    return (a=='primary' and d>='2026-10-29') or (a=='graveyard' and d>='2026-10-21') or (a in('testing','testing2') and '2026-10-19'<=d<='2026-10-22')
rows=[]; keeps={}
for (s,d),g in t.groupby(['strategy','date']):
    g=g.sort_values(['e','symbol'])
    e,x,r=g.e.values,g.x.values,g.r.values
    pm=path_min(e,x,r)
    cens=all(latched_acct(a,d) for a in g.account) and pm<=-2
    row=dict(strategy=s,date=d,n=len(g),pmin=pm,final=r.sum(),cens=cens)
    for L in GRID:
        k=latch_day(e,x,r,L); row[f'R{L}']=r[k].sum(); row[f'n{L}']=int(k.sum())
    rows.append(row)
M=pd.DataFrame(rows); M.to_parquet(f'live_mat{V}.parquet')
print(M.shape, M.cens.sum(), (M.pmin<=-2).sum())
print(M.groupby('strategy').agg(days=('date','size'),n=('n','sum'),R=('final','sum'),touch2=('pmin',lambda v:(v<=-2).sum()),cens=('cens','sum')).to_string())
