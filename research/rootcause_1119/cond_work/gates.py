import sys; sys.path.insert(0,'.'); import pandas as pd,numpy as np; from tab import *
pd.set_option('display.width',230)
L=pd.read_pickle('live_feat.pkl').rename(columns={'strategy':'setup'})
A=cap3(pd.read_pickle('lab_feat.pkl').rename(columns={'r':'R'}))
A['split']=np.where(A.date<='2025-12-31','TRAIN',np.where(A.date<='2026-10-05','VALID','FWD'))
L['split']='LIVE'
G={'G1 counter-compass block':lambda d: d.cmp=='AGAINST',
   'G2 falling-knife (mkt-side SPY 30m <= -0.5%)':lambda d: (d.mkt_side*d.spy_30)<=-0.5,
   'G3 SPY from-open against <= -1.0%':lambda d: (d.mkt_side*d.spy_fo)<=-1.0,
   'G4 no shorts of inverse ETFs':lambda d: d.inverse&(d.side<0),
   'G5 no inverse-ETF shorts while DOWN-confirmed':lambda d: d.inverse&(d.side<0)&(d.W==-2)}
KEY=['ST7-rsi50dn-long-pm-t1s1-FD','L3-gap-slope-fromopen-FD']
rows=[]
for gname,f in G.items():
    for sp,df in list(A.groupby('split'))+[('LIVE',L)]:
        rm=f(df).fillna(False).astype(bool)
        per=df.assign(rm=rm).groupby('setup').apply(lambda g: pd.Series(dict(n=len(g),nrm=int(g.rm.sum()),base=g.R.sum(),delta=-g.R[g.rm].sum())),include_groups=False)
        aff=per[per.nrm>0]
        r=dict(gate=gname,split=sp,setups_aff=len(aff),improve=int((aff.delta>0).sum()),worse=int((aff.delta<0).sum()),
               gain_R=round(aff.delta[aff.delta>0].sum(),1),loss_R=round(aff.delta[aff.delta<0].sum(),1),net=round(aff.delta.sum(),1),
               removed=int(rm.sum()),removed_avgR=round(df.R[rm].mean(),3) if rm.any() else np.nan)
        for k in KEY:
            r[k[:3]]=f"{per.delta.get(k,0):+.1f} ({int(per.nrm.get(k,0))})"
        rows.append(r)
out=pd.DataFrame(rows); print(out.to_string()); out.to_csv('gates.csv',index=False)
