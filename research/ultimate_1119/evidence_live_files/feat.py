import os, sys, numpy as np, pandas as pd, re
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from alpaca.data.enums import Adjustment, DataFeed
W='/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/ev1119/w'
dc=StockHistoricalDataClient(os.environ["ALPACA_API_KEY"], os.environ["ALPACA_SECRET_KEY"])
TZ='America/New_York'
t=pd.read_parquet(W+'/trades.parquet')
t['sig']=pd.to_datetime(t.signal_time.str.replace('T',' '),utc=True,format='mixed').dt.tz_convert(TZ)
t['ent']=pd.to_datetime(t.entry_time.astype(str).str.replace('T',' '),utc=True,format='mixed').dt.tz_convert(TZ)
t['ext']=pd.to_datetime(t.exit_time.astype(str).str.replace('T',' '),utc=True,format='mixed').dt.tz_convert(TZ)
syms=sorted(set(t.symbol)|{'SPY','QQQ'})
def bars(symbols,start,end,tf,batch=200):
    def one(i):
        req=StockBarsRequest(symbol_or_symbols=symbols[i:i+batch],timeframe=tf,start=start,end=end,adjustment=Adjustment.SPLIT,feed=DataFeed('sip'))
        for a in range(3):
            try: return dc.get_stock_bars(req).df
            except Exception as e:
                if a==2: print('fail',i,e,flush=True)
        return pd.DataFrame()
    with ThreadPoolExecutor(6) as ex:
        out=[d for d in ex.map(one,range(0,len(symbols),batch)) if not d.empty]
    return pd.concat(out) if out else pd.DataFrame()
# daily
if not os.path.exists(W+'/daily.parquet'):
    d=bars(syms,datetime(2026,8,1),datetime(2026,11,19),TimeFrame.Day)
    d=d.reset_index(); d['day']=pd.to_datetime(d.timestamp).dt.tz_convert(TZ).dt.date.astype(str)
    d[['symbol','day','open','high','low','close','volume']].to_parquet(W+'/daily.parquet')
d=pd.read_parquet(W+'/daily.parquet').sort_values(['symbol','day'])
g=d.groupby('symbol')
d['pc']=g.close.shift(1)
tr=np.maximum(d.high-d.low,np.maximum((d.high-d.pc).abs(),(d.low-d.pc).abs()))
d['tr']=tr
d['atr']=d.groupby('symbol').tr.transform(lambda s:s.shift(1).rolling(14,min_periods=10).mean())
d['adv']=(d.close*d.volume).groupby(d.symbol).transform(lambda s:s.shift(1).rolling(20,min_periods=10).mean())
d['avgvol']=d.groupby('symbol').volume.transform(lambda s:s.shift(1).rolling(20,min_periods=10).mean())
d['sma20']=d.groupby('symbol').close.transform(lambda s:s.shift(1).rolling(20,min_periods=15).mean())
d['ret5d']=d.groupby('symbol').close.transform(lambda s:s.shift(1)/s.shift(6)-1)
D=d.set_index(['symbol','day'])
def rsi(c,n=5):
    dd=c.diff(); up=dd.clip(lower=0).ewm(alpha=1/n,adjust=False).mean(); dn=(-dd.clip(upper=0)).ewm(alpha=1/n,adjust=False).mean()
    return 100-100/(1+up/dn.replace(0,np.nan))
rows=[]
for day,tg in t.groupby('date'):
    ss=sorted(set(tg.symbol)|{'SPY','QQQ'})
    s=pd.Timestamp(day+' 09:30',tz=TZ); e=pd.Timestamp(day+' 16:00',tz=TZ)
    m=bars(ss,s.to_pydatetime(),e.to_pydatetime(),TimeFrame.Minute)
    if m.empty: print('nobars',day); continue
    m=m.reset_index(); m['ts']=pd.to_datetime(m.timestamp).dt.tz_convert(TZ)
    m=m[(m.ts>=s)&(m.ts<e)]
    M={k:v.set_index('ts').sort_index() for k,v in m.groupby('symbol')}
    P={}
    for k,b in M.items():
        c=b.close; v=b.volume
        c5=c.resample('5min',label='right',closed='left').last().dropna()  # label = bar close time
        r5=rsi(c5); r5.index=r5.index-pd.Timedelta(minutes=1)  # available after last 1-min bar of the 5-min window
        P[k]=dict(ts=(b.index+pd.Timedelta(minutes=1)).values,o=b.open.iloc[0],c=c.values,
                  vw=((c*v).cumsum()/v.cumsum().replace(0,np.nan)).values,r5=r5.reindex(b.index,method='ffill').values,
                  r1=rsi(c).values,hi=b.high.cummax().values,lo=b.low.cummin().values,cv=v.cumsum().values,
                  v15=v.rolling(15,min_periods=1).sum().values)
    def state(sym,at):
        q=P.get(sym)
        if q is None: return None
        i=np.searchsorted(q['ts'],np.datetime64(at.tz_convert('UTC').tz_localize(None)),side='right')-1
        if i<1: return None
        o=q['o']
        return dict(o=o,c=q['c'][i],vw=q['vw'][i],r5=q['r5'][i],r1=q['r1'][i] if i>=5 else np.nan,hi=q['hi'][i],lo=q['lo'][i],
                    c30=q['c'][i-30] if i>=30 else o,c15=q['c'][i-15] if i>=15 else o,cumv=q['cv'][i],v15=q['v15'][i],el=i+1)
    for _,r in tg.iterrows():
        at=r.sig
        st=state(r.symbol,at); sp=state('SPY',at); qq=state('QQQ',at)
        try: pr=D.loc[(r.symbol,day)]
        except KeyError: pr=None
        try: spr=D.loc[('SPY',day)]
        except KeyError: spr=None
        f=dict(id=r.id,account=r.account)
        if st and pr is not None and pr.atr>0:
            A=pr.atr; el=(at-s).total_seconds()/60
            f.update(px=st['c'],gap_pct=(st['o']/pr.pc-1)*100,gap_atr=(st['o']-pr.pc)/A,fo_atr=(st['c']-st['o'])/A,
                     vw_atr=(st['c']-st['vw'])/A,rsi5=st['r5'],rsi1=st['r1'],atr_pct=A/pr.pc*100,adv=pr.adv,
                     rvol=st['cumv']/max(pr.avgvol*min(el,390)/390,1),rvol15=st['v15']*26/max(pr.avgvol,1),
                     rng_atr=(st['hi']-st['lo'])/A,pos_rng=(st['c']-st['lo'])/max(st['hi']-st['lo'],1e-9),
                     m30_atr=(st['c']-st['c30'])/A,m15_atr=(st['c']-st['c15'])/A,
                     dsma20=(st['c']/pr.sma20-1)*100,ret5d=pr.ret5d*100,dpc_atr=(st['c']-pr.pc)/A)
        if sp and spr is not None:
            f.update(spy_fo=(sp['c']/sp['o']-1)*100,spy_gap=(sp['o']/spr.pc-1)*100,spy_m30=(sp['c']/sp['c30']-1)*100,
                     spy_vw=(sp['c']/sp['vw']-1)*100,spy_rsi5=sp['r5'])
        rows.append(f)
    print(day,len(tg),len(M),flush=True)
pd.DataFrame(rows).to_parquet(W+'/feat.parquet')
