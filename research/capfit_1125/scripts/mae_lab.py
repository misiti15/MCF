import sys, numpy as np, pandas as pd, pyarrow.dataset as pads
from multiprocessing import Pool
from pathlib import Path
sys.path.insert(0,sys.argv[1]+'/research/ultimate_1119/top10'); sys.path.insert(0,sys.argv[1])
import bench10 as B
TZ="America/New_York"; LOCK=("2024-11-01","2025-02-28")
HIST,FRESH=Path("/home/user/MCF/data/cache_hist/1Min"),Path("/home/user/MCF/data/cache_fresh/1Min")
P='/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/pyramid'
def load(sym,src):
    p=src/f"{sym}.parquet"
    if not p.exists(): return None
    f=pads.field("__index_level_0__")
    flt=(f<pd.Timestamp(LOCK[0],tz=TZ))|(f>=pd.Timestamp("2025-03-01",tz=TZ))
    b=pads.dataset(str(p),format="parquet").to_table(filter=flt,columns=["high","low","__index_level_0__"]).to_pandas()
    if "__index_level_0__" in b.columns: b=b.set_index("__index_level_0__")
    b.index=pd.DatetimeIndex(b.index).tz_convert(TZ); b=b.sort_index()
    d=b.index.date.astype(str); assert not ((d>=LOCK[0])&(d<=LOCK[1])).any()
    return b
def job(a):
    sym,T=a; out=[]
    for src,sub in ((HIST,T[T.date>="2024-09-16"]),(FRESH,T[T.date<"2024-09-16"])):
        if not len(sub): continue
        b=load(sym,src)
        if b is None: continue
        day=b.index.date.astype(str); mins=b.index.hour*60+b.index.minute
        H,Lo=b.high.to_numpy(float),b.low.to_numpy(float)
        for r in sub.itertuples():
            ix=np.flatnonzero((day==r.date)&(mins>r.em)&(mins<=min(r.xm,955)))
            if not len(ix): out.append((r.Index,0.0)); continue
            adv=(r.entry-Lo[ix].min()) if r.side>0 else (H[ix].max()-r.entry)
            out.append((r.Index,-max(0.0,adv)/r.risk))
    return out
if __name__=='__main__':
    sys.path.insert(0,'.')
    etb=pd.read_parquet(P+'/S/etb_rate.parquet').rate
    parts=[]
    for f in ['fit','check','t2']:
        x=pd.read_parquet(f'{P}/L1/trades_{f}.parquet'); x=x[x.kind_=='prim'].rename(columns={'cfg':'setup'}); parts.append(x)
    for f in ['t1','t2']:
        x=pd.read_parquet(f'{P}/S/work/trades_{f}.parquet'); x=x[~x.setup.str.endswith('|RND')&(x.setup!='L3-gap-slope-fromopen-FD')]; parts.append(x)
    T=pd.concat(parts,ignore_index=True); T['date']=T.date.astype(str)
    T=T[((T.date>="2023-01-03")&(T.date<="2024-09-13"))|((T.date>="2024-10-01")&(T.date<="2024-10-31"))|(T.date>="2025-03-01")]
    T=B.add_r(T)
    home={'L3-gap-slope-fromopen-FD':'primary','RW3-gapdn-rsi5pop-flowsell-short-FD':'primary','RW5-heat30-flowsell-rsi5pop-gapdn-short-FD':'primary','NM-ETF-late-dip-di-long':'primary'}
    bk=[]
    for s,g in T.groupby('setup'):
        rules=dict(B.BOOK[home.get(s,'testingd')]); rules['latch']=None; bk.append(B.book(g,rules,etb))
    T=pd.concat(bk,ignore_index=True)
    jobs=[(s,g) for s,g in T.groupby('symbol')]
    mae={}
    print('booked',len(T),len(jobs),flush=True)
    if True:
        for k,res in enumerate(map(job,jobs)):
            for i,v in res: mae[i]=v
            if k%100==0: print(k,len(jobs),flush=True)
    T['mae']=pd.Series(mae)
    T[['setup','symbol','date','side','entry','risk','r','r_gross','stop_cost_r','kind','mae']].to_parquet('lab_mae.parquet')
    print(T.mae.notna().mean(), len(T))
