import pandas as pd, numpy as np, sys
short=lambda s:s[:30]
def tab(t,sc,label,cost):
    print(f'\n=== MAE angle, {label} ===')
    rows=[]
    for s,g in t[t.mae.notna()].groupby(sc):
        d={'setup':short(s),'n':len(g),'avgR':round(g.r.mean(),3),'P(>=0)':round((g.r>=0).mean(),2)}
        for x in [0.25,0.5,0.75]:
            tc=g.mae<=-x; h=g[tc]
            rt=-x-cost(h)
            d[f'T{x}']=round(tc.mean(),2); d[f'P{x}']=round((h.r>=0).mean(),2) if len(h) else np.nan
            d[f'dR{x}']=round((rt-h.r).sum(),1); d[f'win_cut{x}']=int((h.r>0).sum())
        rows.append(d)
    D=pd.DataFrame(rows); print(D.to_string(index=False))
    for x in [0.25,0.5,0.75]:
        print(x,'setups where tighter stop at -x would add R:',int((D[f'dR{x}']>0).sum()),'of',len(D),'; total dR',round(D[f'dR{x}'].sum(),1))
L=pd.read_parquet('lab_mae.parquet')
tab(L,'setup','lab (bench10 lots, 2023-24 + FIT + CHECK, 1-min bars, LR8)',lambda h:h.stop_cost_r.values)
L['per']=np.where(L.date>='2025-10-01','CHECK',np.where(L.date>='2024-10-01','FIT','T2'))
for p in ['T2','FIT','CHECK']:
    X=L[L.per==p]; 
    print(p,{short(s):(round((g[g.mae<=-0.5].r>=0).mean(),2),round(((-0.5-g[g.mae<=-0.5].stop_cost_r)-g[g.mae<=-0.5].r).sum(),1)) for s,g in X.groupby('setup')})
try:
    V=pd.read_parquet('live_mae.parquet'); print('live coverage',V.mae.notna().mean())
    tab(V,'strategy','live (journals 10-06..11-24, 1-min bars where cached)',lambda h:0.05)
except Exception as e: print(e)
