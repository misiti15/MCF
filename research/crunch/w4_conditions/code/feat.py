"""W4 point-in-time features per live trade. Educational only - not financial advice.
Streams one 1-minute pack per session from the public bars-YYYY-MM release, keeps only the traded names + SPY, deletes it."""
import pandas as pd, numpy as np, os, subprocess, re, io
from datetime import date
LOCK_A, LOCK_B = date(2024,11,1), date(2025,2,28)
U="https://github.com/misiti15/MCF/releases/download"
def get(tag,name,out):
    subprocess.run(['curl','-sSLf','-o',out,f'{U}/{tag}/{name}'],check=True)
t=pd.read_pickle('trades.pkl'); t=t[t.date<='2026-11-17']
# daily priors from three 1day packs (each holds ~50 days before its session)
dl=[]
for d in ['2026-10-06','2026-10-30','2026-11-17']:
    p=f'dl/1day-{d}.parquet'; get(f'bars-{d[:7]}',f'1day-{d}.parquet',p); dl.append(pd.read_parquet(p)); os.remove(p)
D=pd.concat(dl).drop_duplicates(['symbol','ts'],keep='last')
D['day']=D.ts.dt.tz_convert('America/New_York').dt.date.astype(str)
assert not ((D.day>=str(LOCK_A))&(D.day<=str(LOCK_B))).any()
D=D.sort_values(['symbol','day'])
g=D.groupby('symbol')
D['pc']=g.close.shift(1)
tr=np.maximum(D.high,D.pc)-np.minimum(D.low,D.pc)
D['tr']=tr
D['atr14']=g.tr.transform(lambda s:s.shift(1).rolling(14,min_periods=10).mean())   # prior days only
D['dv']=D.close*D.volume
D['adv20']=g.dv.transform(lambda s:s.shift(1).rolling(20,min_periods=10).mean())
D['pday']=(D.pc/g.close.shift(2)-1)*100
D=D.set_index(['symbol','day'])[['pc','atr14','adv20','pday']]
uni=subprocess.run(['git','-C','/home/user/MCF','show','origin/mcf-data:universe.csv'],capture_output=True,text=True).stdout
un=pd.read_csv(io.StringIO(uni))
etfre=re.compile(r'\bETF\b|\bFund\b|ProShares|iShares|Direxion|SPDR|Invesco QQQ|\b[23]X\b|Leveraged|Ultra|Bull|Bear|Trust Series|ETN',re.I)
etf=set(un.symbol[un.name.fillna('').str.contains(etfre)])
rows=[]
for d,td in t.groupby('date'):
    p=f'dl/1min-{d}.parquet'
    try: get(f'bars-{d[:7]}',f'1min-{d}.parquet',p)
    except Exception as e: print('miss',d); continue
    syms=set(td.symbol)|{'SPY'}
    m=pd.read_parquet(p,filters=[('symbol','in',list(syms))]); os.remove(p)
    m['symbol']=m.symbol.astype(str); m=m.sort_values(['symbol','ts'])
    m['end']=m.ts+pd.Timedelta(minutes=1)
    m['pv']=(m.high+m.low+m.close)/3*m.volume
    m['cpv']=m.groupby('symbol').pv.cumsum(); m['cv']=m.groupby('symbol').volume.cumsum()
    m['hh']=m.groupby('symbol').high.cummax(); m['ll']=m.groupby('symbol').low.cummin()
    o=m.groupby('symbol').open.first()
    t0=pd.Timestamp(d+' 09:30',tz='America/New_York').tz_convert('UTC')
    t10=t0+pd.Timedelta(minutes=30)
    spy=m[m.symbol=='SPY'].set_index('end')
    for r in td.itertuples():
        s=m[(m.symbol==r.symbol)&(m.end<=r.sig)]
        if s.empty or r.symbol not in o.index: continue
        last=s.iloc[-1]; px=last.close; op=o[r.symbol]
        k=(r.symbol,d)
        pc,atr,adv,pday=(D.loc[k].values if k in D.index else (np.nan,)*4)
        atrp=atr/pc*100 if pc==pc else np.nan
        sp=spy[spy.index<=min(r.sig,t10)]
        spy10=(sp.close.iloc[-1]/o['SPY']-1)*100 if len(sp) else 0.0
        f30=s[s.end<=t10]
        rng=(f30.high.max()-f30.low.min()) if len(f30) else (last.hh-last.ll)
        vw=last.cpv/last.cv if last.cv>0 else px
        rows.append(dict(id=r.id,acct=r.acct,tod=(r.sig-t0).total_seconds()/60,gap=(op/pc-1)*100,spy10=spy10,
            atr_pct=atrp,price=px,adv=np.log10(adv) if adv and adv>0 else np.nan,etf=int(r.symbol in etf),
            withday=r.side*(px/op-1)*100,vwap=r.side*(px-vw)/atr if atr else np.nan,open=r.side*(px-op)/atr if atr else np.nan,
            pday=pday,or30=rng/atr if atr else np.nan))
    print(d,len(td),len(rows),flush=True)
F=pd.DataFrame(rows)
F.to_pickle('feat.pkl'); print(F.describe().T)
