"""Rebuild RSI-derived frame columns under A-SR and A-GA; store only rows that differ from the as-is rebuild. Open dates only."""
import sys, numpy as np, pandas as pd, os, time
sys.path.insert(0,'/home/user/MCF')
from mcf.data.bars import resample
from mcf.data.store import BarStore
OUT='/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/st7w/rsi'
LK=('2024-11-01','2025-02-28')
def rsi_from_d(d, n, day=None):
    g=d.clip(lower=0); l=-d.clip(upper=0)
    if day is None:
        G=g.rolling(n).sum(); L=l.rolling(n).sum()
    else:
        G=g.groupby(day).transform(lambda s:s.rolling(n,min_periods=1).sum()); L=l.groupby(day).transform(lambda s:s.rolling(n,min_periods=1).sum())
        cnt=d.notna().astype(int).groupby(day).transform(lambda s:s.rolling(n,min_periods=1).sum())
        G=G.where(cnt>0); L=L.where(cnt>0)
    r=100-100/(1+G/L.replace(0,np.nan))
    return r.where((L!=0)|L.isna(),100.0)
def derived(rsi,rsi5,h,l):
    f=pd.DataFrame({'rsi':rsi,'rsi5':rsi5})
    f['rsiSlope']=rsi-rsi.shift(3)
    hi20,lo20=h.rolling(20).max(),l.rolling(20).min()
    f['bear_div']=((h>=hi20)&(rsi<rsi.rolling(20,min_periods=1).max()-5)).astype(np.int8)
    f['bull_div']=((l<=lo20)&(rsi>rsi.rolling(20,min_periods=1).min()+5)).astype(np.int8)
    r=rsi.fillna(50)
    f['rsiHeat']=np.select([r>=80,r>=70,r<=20,r<=30,r<45,r>55],[-25,-((r-70)/10)*20,25,((30-r)/10)*20,(45-r)/15*10,(55-r)/15*10],0)
    return f
COLS=['rsi','rsi5','rsiSlope','bear_div','bull_div','rsiHeat']
def one(args):
    k,syms=args; store=BarStore('/home/user/MCF/data/cache_hist'); res={'SR':[],'GA':[]}; chk=[]
    for s in syms:
        df=store.load(s)
        if df.empty: continue
        ds=pd.Series(df.index.strftime('%Y-%m-%d'),index=df.index)
        df=df[(ds<LK[0])|(ds>LK[1])]          # locked block dropped before any computation
        d5=resample(df,'5min')
        if len(d5)<300: continue
        c,h,l,o=d5.close,d5.high,d5.low,d5.open
        day=pd.Series(d5.index.date,index=d5.index)
        first=(day!=day.shift(1))
        d=c.diff()
        base=derived(rsi_from_d(d,14),rsi_from_d(d,5),h,l)
        dsr=d.where(~first)
        sr=derived(rsi_from_d(dsr,14,day),rsi_from_d(dsr,5,day),h,l)
        dga=d.where(~first,c-o)
        ga=derived(rsi_from_d(dga,14),rsi_from_d(dga,5),h,l)
        end=d5.index+pd.Timedelta(minutes=5); tod=end.hour*100+end.minute
        keep=(tod>=950)&(tod<=1500)&(pd.Series(d5.index.strftime('%Y-%m-%d'),index=d5.index)>='2024-10-01').to_numpy()
        for nm,v in (('SR',sr),('GA',ga)):
            diff=np.zeros(len(d5),bool)
            for cc in COLS:
                a=base[cc].to_numpy(float); b=v[cc].to_numpy(float)
                diff|=~((np.abs(a-b)<1e-4)|(np.isnan(a)&np.isnan(b)))
            m=keep&diff
            x=v.loc[m,COLS].astype('float32').copy(); x['symbol']=s; x['date']=day[m].astype(str).to_numpy(); x['tod']=tod[m]
            res[nm].append(x.reset_index(drop=True))
        b=base.loc[keep,['rsi']].copy(); b['symbol']=s; b['date']=day[keep].astype(str).to_numpy(); b['tod']=tod[keep]
        chk.append(b.sample(min(300,len(b)),random_state=1))
    for nm in res:
        if res[nm]: pd.concat(res[nm]).to_parquet(f'{OUT}/{nm}_{k:03d}.parquet',index=False,compression='zstd')
    if chk: pd.concat(chk).to_parquet(f'{OUT}/chk_{k:03d}.parquet',index=False)
    return k
if __name__=='__main__':
    from multiprocessing import Pool
    syms=BarStore('/home/user/MCF/data/cache_hist').symbols()
    if len(sys.argv)>1: syms=syms[:int(sys.argv[1])]
    jobs=[(i//40,syms[i:i+40]) for i in range(0,len(syms),40)]
    t0=time.time()
    with Pool(4) as p:
        for k in p.imap_unordered(one,jobs): print(k,f'{time.time()-t0:.0f}s',flush=True)
