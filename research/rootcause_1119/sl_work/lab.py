"""2-year lab scan of L3-gap-slope-fromopen-FD and ST7-rsi50dn-long-pm-t1s1-FD, open history only (locked block never read).
All qualifying bars kept (fire flag) plus first-per-symbol-day; production-cost R via gates.prod_r (LR-style lab costs)."""
import sys, importlib.util, numpy as np, pandas as pd, time
sys.path.insert(0,'/home/user/MCF'); sys.path.insert(0,'/home/user/MCF/research/history2y')
from lib import load_month, months
from mcf.research import gates as G
def load(p,n):
    s=importlib.util.spec_from_file_location(n,p); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
L3=load('/home/user/MCF/research/bdi/fullday/L3-gap-slope-fromopen-FD.py','l3')
ST7=load('/home/user/MCF/research/bdi/fullday/ST7-rsi50dn-long-pm-t1s1-FD.py','st7')
S=[('L3',L3,'short',0.0),('ST7',ST7,'long',95e6)]
cols=['symbol','date','tod','close','atr_d','vwapDistPct','dist_hod_atr','dist_lod_atr','dist_pdh_atr','dist_pdl_atr','rsi','fromOpen','buyPressure','gap','sma20_slope_pct','adv20','r_short_t1s1','win_short_t1s1','r_long_t1s1','win_long_t1s1']
out=[];t0=time.time()
for mo in months():
    df=load_month(mo,columns=cols)
    tod=df.tod.to_numpy(); adv=df.adv20.fillna(0).to_numpy()
    for name,m,side,mina in S:
        base=(tod>=950)&(tod<=1500)&(adv>=mina)
        mk=np.asarray(m.mask(df),bool)&base&np.isfinite(df[f'r_{side}_t1s1'].to_numpy(float))&(df.atr_d.to_numpy(float)>0)
        if name=='L3':  # prefilter gap_le same as mask clause
            pass
        idx=np.flatnonzero(mk)
        r=G.prod_r(df[f'r_{side}_t1s1'].to_numpy(float)[idx],df[f'win_{side}_t1s1'].to_numpy(float)[idx],df.close.to_numpy(float)[idx],df.atr_d.to_numpy(float)[idx],'t1s1',tod=df.tod.to_numpy(float)[idx])
        x=pd.DataFrame({'setup':name,'date':df.date.to_numpy()[idx],'symbol':df.symbol.astype(str).to_numpy()[idx],'tod':tod[idx],'r':r,'close':df.close.to_numpy()[idx],'gap':df.gap.to_numpy()[idx],'fromOpen':df.fromOpen.to_numpy()[idx]})
        out.append(x)
    print(mo,len(df),f'{time.time()-t0:.0f}s',flush=True); del df
x=pd.concat(out,ignore_index=True)
x['first']=~x.duplicated(['setup','symbol','date'])
x.to_parquet('lab_fires.parquet')
