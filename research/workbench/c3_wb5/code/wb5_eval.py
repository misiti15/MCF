# WB5 split check (pre-registered tunes from research/consultant_p3/RESULTS.md #7; C3-WB pass rule on the LATER sessions).
import pandas as pd, numpy as np, math, json
S=__import__('os').environ.get('WB5_DIR','wb5')
NY='America/New_York'
t=pd.read_parquet(S+'/trades.parquet')
for c in ('signal_time','entry_time','exit_time'):
    t[c]=pd.to_datetime(t[c],utc=True,format='ISO8601',errors='coerce').dt.tz_convert(NY)
t['date']=t.date.astype(str)
dl=pd.read_parquet(S+'/daily.parquet'); dl['d']=pd.to_datetime(dl.timestamp).dt.tz_convert(NY).dt.strftime('%Y-%m-%d')
dl=dl.sort_values(['symbol','d']); dl['pc']=dl.groupby('symbol').close.shift(1)
D=dl.set_index(['symbol','d'])
ix=pd.read_parquet(S+'/idx1m.parquet'); ix['ts']=pd.to_datetime(ix.timestamp).dt.tz_convert(NY)
sm=pd.read_parquet(S+'/sym1m.parquet'); sm['ts']=pd.to_datetime(sm.timestamp).dt.tz_convert(NY)
_cache={}
def _grp(frame):
    k=id(frame)
    if k not in _cache:
        f=frame.copy(); f['d']=f.ts.dt.strftime('%Y-%m-%d')
        f=f[(f.ts.dt.time>=pd.Timestamp('09:30').time())&(f.ts.dt.time<pd.Timestamp('16:00').time())]
        _cache[k]={kk:g.set_index('ts').sort_index() for kk,g in f.groupby(['symbol','d'])}
    return _cache[k]
def mbars(frame,sym,day):
    return _grp(frame).get((sym,day), pd.DataFrame(columns=['open','high','low','close']))
def last_close_before(frame,sym,day,ts):
    g=mbars(frame,sym,day); g=g[g.index+pd.Timedelta(minutes=1)<=ts]
    return None if g.empty else float(g.close.iloc[-1])
def day_open(frame,sym,day):
    g=mbars(frame,sym,day); return None if g.empty else float(g.open.iloc[0])
def dec(r): return r.signal_time if pd.notna(r.signal_time) else r.entry_time
def stats(x):
    if len(x)==0: return dict(n=0,avg=None,wo=None,worst=None,total=0.0)
    bd=x.groupby('date').R2.sum(); best=bd.idxmax()
    rest=x[x.date!=best]
    return dict(n=len(x),days=int(x.date.nunique()),avg=round(x.R2.mean(),3),total=round(x.R2.sum(),2),
                wo=round(rest.R2.mean(),3) if len(rest) else None,worst=round(bd.min(),2),best_share=round(bd.max()/x.R2.sum(),2) if x.R2.sum()>0 else None)
def verdict(par,cp):
    if cp['n']==0: return 'FAIL (no check trades)'
    a,b=par['avg'],cp['avg']
    meets = b>=a-0.01 or (a>0 and b>=0.95*a)
    wo_ok = par['wo'] is None or cp['wo'] is None or cp['wo']>=par['wo']-max(0.02,0.10*abs(par['wo']))
    w_ok = cp['worst']>=par['worst']-max(0.02,0.10*abs(par['worst']))
    return 'PASS' if (meets and wo_ok and w_ok) else 'FAIL'+('' if meets else ' avgR')+('' if wo_ok else ' w/o-best')+('' if w_ok else ' worst-day')
res={}
def run(name,par,keep_fn=None,r2_fn=None):
    x=t[t.strategy==par].copy().sort_values('entry_time')
    days=sorted(x.date.unique()); k=math.ceil(len(days)/2); fitd=set(days[:k])
    x['half']=np.where(x.date.isin(fitd),'fit','check')
    x['R2']=x.R
    y=x.copy()
    if keep_fn is not None: y=y[y.apply(keep_fn,axis=1)]
    if r2_fn is not None: y['R2']=y.apply(r2_fn,axis=1)
    out={}
    for h in ('fit','check'):
        pp=stats(x[x.half==h]); cc=stats(y[y.half==h]); out[h]={'parent':pp,'copy':cc}
    out['check_verdict']=verdict(out['check']['parent'],out['check']['copy'])
    u=x[x.date=='2026-11-18']; uc=y[y.date=='2026-11-18']
    out['unseen_1118']={'parent':stats(u),'copy':stats(uc)}
    out['fit_days']=sorted(fitd); out['check_days']=[d for d in days if d not in fitd]
    res[name]=out
# T1 CWT09 g10 -> g15 + signal-bar close below the day open
def k1(r):
    d=dec(r); o=day_open(sm,r.symbol,r.date); c=last_close_before(sm,r.symbol,r.date,d)
    try: pc=D.loc[(r.symbol,r.date),'pc']; op=D.loc[(r.symbol,r.date),'open']
    except KeyError: return False
    gap=(op/pc-1)*100
    return bool(gap<=-15 and o is not None and c is not None and c<o)
run('T1 CWT09-g15+belowopen','CWT09-gapdn-vwaploss-g10-short',k1)
# T2 NS3 09:50-10:30 + SPY and QQQ up on the day at the decision bar
def up(sym,day,ts):
    c=last_close_before(ix,sym,day,ts)
    g=dl[(dl.symbol==sym)]
    return None
spy_pc={}; 
idd=ix.copy(); idd['d']=idd.ts.dt.strftime('%Y-%m-%d')
rth=idd[(idd.ts.dt.time>=pd.Timestamp('09:30').time())&(idd.ts.dt.time<pd.Timestamp('16:00').time())]
closes=rth.groupby(['symbol','d']).close.last().reset_index().sort_values(['symbol','d']); closes['pc']=closes.groupby('symbol').close.shift(1)
PC=closes.set_index(['symbol','d']).pc
def k2(r):
    d=dec(r); tm=d.time()
    if not (pd.Timestamp('09:50').time()<=tm<pd.Timestamp('10:30').time()): return False
    for s in ('SPY','QQQ'):
        c=last_close_before(ix,s,r.date,d); pc=PC.get((s,r.date))
        if c is None or pc is None or not (c>pc): return False
    return True
run('T2 NS3 0950-1030+SPY/QQQ up','NS3-failed-vwap-reclaim-short',k2)
# T3 MF2-FD / MF4-FD + NM-MF3 2-part gate: QQQ below its open at the decision bar AND the stock did not gap up
def k3(r):
    d=dec(r); c=last_close_before(ix,'QQQ',r.date,d); o=day_open(ix,'QQQ',r.date)
    try: pc=D.loc[(r.symbol,r.date),'pc']; op=D.loc[(r.symbol,r.date),'open']
    except KeyError: return False
    return bool(c is not None and o is not None and c<o and op<=pc)
run('T3a MF2-FD+NM-MF3 gate','MF2-open-rsimidhi-flowsell-FD',k3)
run('T3b MF4-FD+NM-MF3 gate','MF4-h40-open-flowsell-FD',k3)
# T4 GEN-261027-08: one exit change = 1R target (traded THROUGH by max(1c,0.03%), fill at the limit; else live exit)
def r4(r):
    g=mbars(sm,r.symbol,r.date); risk=abs(r.entry-r.stop); side=int(r.side)
    tgt=r.entry+side*risk
    g=g[(g.index>=r.entry_time.floor('1min')+pd.Timedelta(minutes=1))&(g.index<r.exit_time.floor('1min'))]
    thr=max(0.01,0.0003*tgt)
    for ts,b in g.iterrows():
        # stop first inside a bar (live exits already include it: if the bar hits the stop, live stopped there)
        if (side==-1 and b.high>=r.stop) or (side==1 and b.low<=r.stop): break
        if (side==-1 and b.low<=tgt-thr) or (side==1 and b.high>=tgt+thr):
            px=float(b.open) if ((side==-1 and b.open<tgt) or (side==1 and b.open>tgt)) else tgt
            new=r.pnl_adj+side*(px-r.exit)*r.shares
            return new/(risk*r.shares)
    return r.R
run('T4 GEN-261027-08 1R target','GEN-261027-08-ORBfailDn-FromPCATRlem0p96-LUNCH-QQQltm0p6-hold-short',None,r4)
# T5 L3-rsi5hi-FD refire off (first entry per symbol-day)
first=t[t.strategy=='L3-gap-slope-rsi5hi-FD'].sort_values('entry_time').groupby(['symbol','date']).head(1).index
run('T5 L3-rsi5hi-FD refire off','L3-gap-slope-rsi5hi-FD',lambda r: r.name in set(first))
json.dump(res,open(S+'/wb5_results.json','w'),indent=1,default=str)
for k,v in res.items():
    print(k, v['check_verdict'])
    for h in ('fit','check'):
        print('  ',h,'parent',v[h]['parent'],'\n     copy',v[h]['copy'])
    print('   1118 parent',v['unseen_1118']['parent'].get('total'),v['unseen_1118']['parent'].get('n'),'copy',v['unseen_1118']['copy'].get('total'),v['unseen_1118']['copy'].get('n'))
