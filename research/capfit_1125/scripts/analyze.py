import pandas as pd, numpy as np, sys
sys.path.insert(0,'.')
from caplib import *
V=sys.argv[1]; K=int(sys.argv[2]) if len(sys.argv)>2 else 8
M=pd.read_parquet(f'live_mat{V}.parquet').sort_values(['strategy','date']).reset_index(drop=True)
M['Rnone']=M.final; M['nnone']=M.n
M['wk']=pd.to_datetime(M.date).dt.strftime('%G-%V')
short=lambda s:s[:34]
pd.set_option('display.width',250)
def R(row,L): return row['Rnone'] if L is None else row[f'R{L}']
def N(row,L): return row['nnone'] if L is None else row[f'n{L}']
if K==8:
  # descriptive (full sample, in-sample)
  print('=== descriptive, all sessions (in-sample) ===')
  out=[]
  for s,g in M.groupby('strategy'):
    d={'setup':short(s),'days':len(g)}
    for L in [-1.0,-1.5,-2.0,-2.5,-3.0,-4.0]:
        tc=g.pmin<=L; d[f'T{L}']=int(tc.sum())
        d[f'Pab{L}']=round((g.final[tc]>L).mean(),2) if tc.any() else np.nan
        d[f'g{L}']=round((g[f'R{L}']-g.Rnone).sum(),1)
    out.append(d)
  D=pd.DataFrame(out); print(D.to_string(index=False))
  print('pooled gain by level:',{L:round((M[f'R{L}']-M.Rnone).sum(),1) for L in GRID})
  print('pooled touch / P(final>L|touch) / P(final>=0|touch):')
  for L in GRID:
      tc=M.pmin<=L; print(L,int(tc.sum()),round((M.final[tc]>L).mean(),2),round((M.final[tc]>=0).mean(),2), 'setups+',int(((M[f'R{L}']-M.Rnone).groupby(M.strategy).sum()>0.05).sum()),'setups-',int(((M[f'R{L}']-M.Rnone).groupby(M.strategy).sum()<-0.05).sum()))
# walk-forward
rows=[]; lv=[]
for s,g in M.groupby('strategy'):
    for w in sorted(g.wk.unique()):
        C=g[g.wk<w]; Tst=g[g.wk==w]
        if len(C)<K: continue
        G={L:(C[f'R{L}']-C.Rnone).sum() for L in GRID}; T={L:int((C.pmin<=L).sum()) for L in GRID}
        p1,p3=calib(G,T); p2=clamp(p1)
        lv.append(dict(setup=short(s),wk=w,ncal=len(C),P1=p1,P3=p3))
        for _,r in Tst.iterrows():
            rows.append(dict(strategy=s,date=r.date,none=R(r,None),u2=R(r,-2.0),P1=R(r,p1),P2=R(r,p2),P3=R(r,p3),
              n_none=N(r,None),n_u2=N(r,-2.0),n_P1=N(r,p1),n_P2=N(r,p2),n_P3=N(r,p3)))
W=pd.DataFrame(rows)
print(f'\n=== walk-forward K={K} variant={V or "L"}: {len(W)} setup-days, {W.strategy.nunique()} setups, {W.date.nunique()} dates ===')
pols=['none','u2','P1','P2','P3']
res=[]
for p in pols:
    dd=W.groupby('date')[p].sum(); ntr=W[f'n_{p}'].sum()
    b=dd.idxmax(); nb=W[W.date==b][f'n_{p}'].sum()
    res.append(dict(pol=p,trades=ntr,R=round(dd.sum(),1),worst=round(dd.min(),1),best=round(dd.max(),1),best_share=round(dd.max()/dd.sum(),2) if dd.sum()>0 else np.nan,
       avg=round(dd.sum()/ntr,3),avg_wo_best=round((dd.sum()-dd.max())/(ntr-nb),3),
       t_vs_none=round(clustered_t((dd-W.groupby('date')['none'].sum()).values),2),t_vs_u2=round(clustered_t((dd-W.groupby('date')['u2'].sum()).values),2)))
print(pd.DataFrame(res).to_string(index=False))
P=W.groupby('strategy')[pols].sum()
for p in ['u2','P1','P2','P3']:
    for base in ['none','u2']:
        if p==base: continue
        dl=P[p]-P[base]
        print(f'{p} vs {base}: improve {int((dl>0.05).sum())} (+{dl[dl>0.05].sum():.1f}), worse {int((dl<-0.05).sum())} ({dl[dl<-0.05].sum():.1f}), same {int((dl.abs()<=0.05).sum())}; worst setup {dl.min():.1f}')
P.index=[short(s) for s in P.index]; print(P.round(1).to_string())
L=pd.DataFrame(lv); print('\nlevels chosen (P1) per setup by week:'); print(L.pivot(index='setup',columns='wk',values='P1').to_string())
print('\nP1 level distribution:',L.P1.value_counts(dropna=False).to_dict())
W.to_csv(f'wf{V}_K{K}.csv',index=False)
