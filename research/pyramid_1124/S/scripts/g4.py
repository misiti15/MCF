"""G4: L3-fromopen with first-minute-VWAP gap <= own threshold (-2.657%). Educational only - not financial advice."""
import pandas as pd, numpy as np, sys
sys.argv=[sys.argv[0],sys.argv[1]]; W=sys.argv[1]
exec(open(W+'/live.py').read().split("out={}")[0])
g=t[(t.strategy==C['G'])&(t.symbol.map(etb).fillna(0)>=.9)].copy()
gp=pd.read_csv(sys.path[0]+'/../../inbox/research/bdi/gapdef_1124/live_gaps.csv.gz')
g=g.merge(gp[['date','symbol','gap_print','gapV']],on=['date','symbol'],how='left')
g=g[g.date>='2026-10-23']
print('trades in gap window',len(g),'missing gapV',int(g.gapV.isna().sum()))
rm=g.gapV.notna()&(g.gapV>-2.6573517322540283)
print('removed',int(rm.sum()),'avg',round(g[rm].r.mean(),3),'dR',round(-g[rm].r.sum(),2))
d=(-g[rm].groupby('date').r.sum()); print('dR by day',d.round(2).to_dict())
if len(d): b=d.idxmax(); print('dR w/o best day',round(d.sum()-d.max(),2),'best share',round(d.max()/d.sum(),2) if d.sum()>0 else None)
print(g[rm][['date','symbol','gap_print','gapV','r']].round(2).to_string(index=False))
# under latch -2 replay
g.index=range(len(g)); g2=g.copy(); g2.loc[rm.values,'r']=np.nan
for L in (None,-2):
    a=g.loc[latch(g,L)[lambda s:s].index]; b=g[~rm.values]; b=b.loc[latch(b,L)[lambda s:s].index]
    print('latch',L,'base R',round(a.r.sum(),2),'G4 R',round(b.r.sum(),2),'base wo',card(a)['wo_best'],'G4 wo',card(b)['wo_best'])
