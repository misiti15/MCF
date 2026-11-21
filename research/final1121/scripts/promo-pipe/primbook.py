"""Apply Primary book rules (cap 30 open lots per setup, <=3 lots/symbol, -2R realized per-setup daily latch) to a
setup's live trades (entry/exit times from the journals). Approximation of a Primary-rules record (not PSHADOW)."""
import pandas as pd, numpy as np, math
t=pd.read_pickle('live.pkl')
t['et']=pd.to_datetime(t.entry_time,utc=True,format='mixed'); t['xt']=pd.to_datetime(t.exit_time,utc=True,format='mixed')
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
def ct(x):
    m=x.r.mean(); e=(x.r-m).groupby(x.date).sum(); se=math.sqrt((e**2).sum())/len(x); return m/se
def rec(x):
    d=x.groupby('date').r.sum(); s=d.sort_values(ascending=False); tot=x.r.sum()
    return dict(n=len(x),sess=d.size,tot=round(tot,1),avg=round(x.r.mean(),3),wo1=round(x[~x.date.isin(s.index[:1])].r.mean(),3),
      wo2=round(x[~x.date.isin(s.index[:2])].r.mean(),3),bshare=round(s.iloc[0]/tot,2) if tot>0 else None,dayt=round(ct(x),2),
      green=round((d>0).mean(),2),worst=round(d.min(),1),shrunk=round(len(x)/(len(x)+150)*x.r.mean()-150/(len(x)+150)*0.1,3))
C=['RW7-gapdn-bounce-early-short-FD','L3-gap-slope-lowdist-FD','L3-gap-slope-rsi5hi-FD','RW1-gapdn-bounce-flowsell-short-FD','CWT09-gapdn-vwaploss-g10-short','RW6-ns2-up3-short-FD',
   'L3-gap-slope-fromopen-FD','RW3-gapdn-rsi5pop-flowsell-short-FD','RW5-heat30-flowsell-rsi5pop-gapdn-short-FD']
rows=[]
out={}
for c in C:
    x=t[t.strategy==c]
    b=book(x); out[c]=b
    rows.append(dict(setup=c[:34],view='raw',**rec(x))); rows.append(dict(setup=c[:34],view='primary-book',**rec(b)))
pd.set_option('display.width',250)
print(pd.DataFrame(rows).to_string(index=False))
pd.to_pickle(out,'primbook.pkl')
