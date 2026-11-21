import pandas as pd, numpy as np, math, json
t=pd.read_pickle('live.pkl')
prim=t[t.account=='primary']
LU=['L3-gap-slope-fromopen-FD','RW3-gapdn-rsi5pop-flowsell-short-FD','RW5-heat30-flowsell-rsi5pop-gapdn-short-FD','NM-ETF-late-dip-di-long','ST7-rsi50dn-long-pm-t1s1-FD']
# Primary-member symbol-days: current members' trades in ANY account + Primary account trades
psd=set(zip(prim.symbol,prim.date))|set(zip(t[t.strategy.isin(LU)].symbol,t[t.strategy.isin(LU)].date))
reps=json.load(open('/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/inbox/docs/live/arena_reps.json'))['setups']
def ct(x):
    m=x.r.mean(); e=(x.r-m).groupby(x.date).sum(); se=math.sqrt((e**2).sum())/len(x); return m/se
def rec(x):
    d=x.groupby('date').r.sum(); s=d.sort_values(ascending=False); tot=x.r.sum(); n=len(x)
    return dict(n=n,sess=d.size,tot=round(tot,1),avg=round(x.r.mean(),3),wo1=round(x[~x.date.isin(s.index[:1])].r.mean(),3),
      wo2=round(x[~x.date.isin(s.index[:2])].r.mean(),3),bday=s.index[0][5:],bshare=round(s.iloc[0]/tot,2) if tot>0 else np.nan,dayt=round(ct(x),2),
      green=round((d>0).mean(),2),shrunk=round(n/(n+150)*x.r.mean()-150/(n+150)*0.1,3))
C=['RW7-gapdn-bounce-early-short-FD','L3-gap-slope-lowdist-FD','L3-gap-slope-rsi5hi-FD','CWT09-gapdn-vwaploss-g10-short','RW1-gapdn-bounce-flowsell-short-FD']
rows=[]
for c in C:
    x=t[t.strategy==c]
    no=x[[(a,b) not in psd for a,b in zip(x.symbol,x.date)]]
    ov=x[[(a,b) in psd for a,b in zip(x.symbol,x.date)]]
    od=x[x.account=='testing']
    for nm,y in (('raw',x),('non-overlap',no),('overlap',ov),('OnDeck-only',od)):
        if len(y)>2: rows.append(dict(setup=c[:30],rec=nm,**rec(y)))
    # halves
    ds=sorted(x.date.unique()); h=ds[len(ds)//2]
    for nm,y in (('1st half',x[x.date<h]),('2nd half',x[x.date>=h])):
        rows.append(dict(setup=c[:30],rec=nm,**rec(y)))
    r=reps.get(c,{}); print(c, 'active',r.get('active_days'),'traded',r.get('traded_days'))
pd.set_option('display.width',250)
R=pd.DataFrame(rows); print(R.to_string(index=False))
# BAR2 / PRIME checks on non-overlap
