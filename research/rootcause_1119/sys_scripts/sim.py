import sqlite3, json, pandas as pd, numpy as np, sys
W='../sys_work'
b=pd.read_parquet(f'{W}/bars_today.parquet'); b['ts']=pd.to_datetime(b.t).dt.tz_convert('America/New_York')
B={s:g.set_index('ts').sort_index() for s,g in b.groupby('symbol')}
c=sqlite3.connect(f'{W}/journal.db')
sig=pd.read_sql("select * from signals where day='2026-11-19' and run_id=1",c)
sig['tsl']=pd.to_datetime(sig.ts,format='ISO8601',utc=True).dt.tz_convert('America/New_York')
def cost(px): return 0.01+px*1e-4
def sim(sym,side,ts,stop,target,qty=None):
    g=B.get(sym)
    if g is None: return None
    t0=ts.floor('min')
    g2=g[g.index>=t0]
    if not len(g2): return None
    e=g2.iloc[0].o; risk=abs(e-stop)
    if risk<=0 or (side==-1 and e>=stop) or (side==1 and e<=stop): return dict(sym=sym,r=np.nan,why='entry beyond stop')
    for t,r in g2.iterrows():
        if t.strftime('%H:%M')>='15:55':
            x=r.o; why='time'; break
        hs = r.h>=stop if side==-1 else r.l<=stop
        ht = (r.l<=target if side==-1 else r.h>=target) if target==target and target else False
        if hs: x=stop; why='stop'; break
        if ht: x=target; why='target'; break
    else:
        x=g2.iloc[-1].c; why='open@'+g2.index[-1].strftime('%H:%M')
    gross=(x-e)*side
    net=gross-cost(e)-cost(x)-(0.02 if why=='stop' else 0)
    return dict(sym=sym,entry=round(e,3),exit=round(x,3),why=why,exit_t=(t.strftime('%H:%M') if why in('stop','target','time') else ''),r=round(net/risk,2))
mode=sys.argv[1]
if mode=='latch':
    s=sig[sig.reason=='setup daily loss limit'].sort_values('tsl')
elif mode=='etb':
    s=sig[sig.reason=='not shortable/ETB'].sort_values('tsl')
elif mode=='actual':
    s=sig[sig.status=='submitted'].sort_values('tsl')
out=[]
for r in s.itertuples():
    res=sim(r.symbol,r.side,r.tsl,r.stop,r.target)
    if res is None: out.append(dict(t=r.tsl.strftime('%H:%M'),sym=r.symbol,st=r.strategy[:4],r=np.nan,why='nobars')); continue
    res.update(t=r.tsl.strftime('%H:%M'),st=r.strategy[:4]); out.append(res)
o=pd.DataFrame(out); pd.set_option('display.width',250); pd.set_option('display.max_rows',300)
print(o.to_string()); print(o.groupby('st').r.agg(['count','sum','mean']))
o.to_csv(f'{W}/sim_{mode}.csv',index=False)
