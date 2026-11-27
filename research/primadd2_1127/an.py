"""PRIMADD2-1127: per-setup records (raw, booked, non-overlap vs Primary members, Primary-book cap30/3-per-symbol/-2R latch, On Deck, PSHADOW). Usage: python an.py ALL.pkl OUT.json. Educational only - not financial advice."""
import pandas as pd, numpy as np, math, json, sys
t=pd.read_pickle(sys.argv[1]); OUT=sys.argv[2]
live=t[t.run_id==1].drop_duplicates('k').copy()
live['et']=pd.to_datetime(live.entry_time,utc=True,format='mixed'); live['xt']=pd.to_datetime(live.exit_time,utc=True,format='mixed')
PRIM=['L3-gap-slope-fromopen-FD','NM-ETF-late-dip-di-long','RW3-gapdn-rsi5pop-flowsell-short-FD','RW5-heat30-flowsell-rsi5pop-gapdn-short-FD']
psd=set(zip(live[live.strategy.isin(PRIM)].symbol,live[live.strategy.isin(PRIM)].date))
C={'L3-lowdist':'L3-gap-slope-lowdist-FD','RW7':'RW7-gapdn-bounce-early-short-FD','L3-rsi5hi':'L3-gap-slope-rsi5hi-FD','RW6':'RW6-ns2-up3-short-FD',
   'GEN-261022-05 (Testing B)':'GEN-261022-05-MACDhge0p079-UpWickge0p71-ORHdistlem0p38-PM-BRoplt0p35-holdtr-short',
   'GEN-261026-07 (Testing A)':'GEN-261026-07-Flow3ge0p56-BBpctge0p98-ADX7le34-PM-BRvwlt0p3-holdtr-short'}
def book(x,cap=30,symcap=3,latch=-2.0):
    x=x.sort_values('et'); keep=[]
    for d,g in x.groupby('date'):
        open_=[]; real=0.0
        for i,r in g.iterrows():
            still=[]
            for (xt,s,rr) in open_:
                if xt<=r.et: real+=rr
                else: still.append((xt,s,rr))
            open_=still
            if latch is not None and real<=latch+1e-12: continue
            if len(open_)>=cap or sum(1 for o in open_ if o[1]==r.symbol)>=symcap: continue
            keep.append(i); open_.append((r.xt,r.symbol,r.r))
    return x.loc[keep]
def rec(x,col='r'):
    if not len(x): return dict(n=0)
    r=x[col]; d=r.groupby(x.date).sum(); s=d.sort_values(ascending=False); tot=r.sum(); n=len(x); m=r.mean()
    e=(r-m).groupby(x.date).sum(); se=math.sqrt((e**2).sum())/n if n>1 else float('nan')
    tt=m/(r.std(ddof=1)/math.sqrt(n)) if n>1 and r.std()>0 else float('nan')
    wo=x[~x.date.isin(s.index[:1])][col]; wo2=x[~x.date.isin(s.index[:2])][col]
    last10=d.sort_index().iloc[-10:].sum()
    return dict(n=n,sess=int(d.size),tot=round(tot,2),avg=round(m,3),wo1=round(wo.mean(),3) if len(wo) else None,wo2=round(wo2.mean(),3) if len(wo2) else None,
        best_day=s.index[0],best_R=round(s.iloc[0],2),share=round(s.iloc[0]/tot,2) if tot>0 else None,t=round(tt,2),dayt=round(m/se,2) if se==se and se>0 else None,
        green=round((d>0).mean(),2),worst=round(d.min(),2),worst_day=d.idxmin(),last10=round(last10,2),shrunk=round(n/(n+150)*m-150/(n+150)*0.1,3),
        d1127=round(d.get('2026-11-27',0.0),2),n1127=int((x.date=='2026-11-27').sum()),first=d.index.min(),last=d.index.max())
res={}
for lab,s in C.items():
    x=live[live.strategy==s]
    acc=x.groupby('account').agg(n=('r','size'),sess=('date','nunique'),R=('r','sum'),d0=('date','min'),d1=('date','max')).round(2)
    od=x[(x.account=='testing')&(x.date>='2026-11-12')]
    no=x[[ (a,b) not in psd for a,b in zip(x.symbol,x.date)]]
    pb=book(x)
    sh=t[(t.run_id==3)&(t.account=='primary')&(t.strategy==s)]
    res[lab]=dict(setup=s,raw=rec(x),booked=rec(x,'r_booked'),nonoverlap=rec(no),nonoverlap_frac=round(len(no)/len(x),2) if len(x) else None,
        primbook=rec(pb),ondeck_traded_sessions=int(od.date.nunique()),ondeck=rec(od),pshadow=rec(sh),
        accounts={k:v for k,v in acc.to_dict('index').items()})
json.dump(res,open(OUT,'w'),indent=1,default=str)
for lab,v in res.items():
    print('==',lab)
    for k in ['raw','booked','nonoverlap','primbook','ondeck','pshadow']: print(' ',k,v[k])
    print('  nonoverlap_frac',v['nonoverlap_frac'],'OD traded sess',v['ondeck_traded_sessions']); print('  accts',v['accounts'])
