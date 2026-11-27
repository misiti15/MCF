"""PYRAMID-S live analyses (pooled, deduped, LR8). Educational only - not financial advice."""
import pandas as pd, numpy as np, heapq, sys, json
W=sys.argv[1]; t=pd.read_pickle(W+'/all.pkl'); t=t[~t.dup].copy()
t['et']=pd.to_datetime(t.entry_time,utc=True,format='mixed'); t['xt']=pd.to_datetime(t.exit_time,utc=True,format='mixed')
t['hold']=(t.xt-t.et).dt.total_seconds()/60
days=sorted(t.date.unique())
book=t[t.account=='primary'].groupby('date').r.sum().reindex(days,fill_value=0)
w10=book.nsmallest(10).index
etb=pd.read_parquet(W+'/etb_rate.parquet').rate
C={'G':'L3-gap-slope-fromopen-FD','N1':'GEN-261029-06-EMAdChgge0p092-DayRngVsPrevle0p61-LATE-QQQltm0p3-t1s1-short',
   'N2':'GEN-261023-06-RSI7le38-Ret15mge0p54-EMAdiffge0p29-LAM-SPYltm0p25-t1s05-short','N3':'ST5-pdbrkup-short-mid-t05s1-FD'}
def latch(g,L):
    g=g.sort_values('et'); keep=pd.Series(True,index=g.index)
    if L is None: return keep
    for d,sub in g.groupby('date'):
        pend=[]; real=0.0
        for i,et,xt,r in zip(sub.index,sub.et,sub.xt,sub.r):
            while pend and pend[0][0]<=et: real+=heapq.heappop(pend)[1]
            if real<=L+1e-12: keep[i]=False; continue
            heapq.heappush(pend,(xt,r))
    return keep
def card(g):
    d=g.groupby('date').r.sum(); dd=d.reindex(days,fill_value=0); tot=d.sum(); b=d.idxmax()
    e=(g.r-g.r.mean()).groupby(g.date).sum(); se=np.sqrt((e**2).sum())/len(g)
    w=g.r[g.r>0].mean(); l=-g.r[g.r<=0].mean()
    return dict(n=len(g),ses=len(d),tps=round(len(g)/len(d),1),avg=round(g.r.mean(),3),win=round((g.r>0).mean(),3),
      be_win=round(l/(w+l),3),wo_best=round(g.r[g.date!=b].mean(),3),best=b,share=round(d.max()/tot,2) if tot>0 else None,
      tot=round(tot,1),tday=round(g.r.mean()/se,2),corr=round(np.corrcoef(dd,book)[0,1],3),w10=round(dd[w10].sum(),1),
      worst=round(d.min(),1),hold=round(g.hold.median(),1))
out={}
print('book worst10',book[w10].round(1).to_dict())
for k,s in C.items():
    g=t[t.strategy==s].copy()
    print('\n==',k,s,'accounts',g.account.value_counts().to_dict(),'non-ETB(rate<.9) trades',int((g.symbol.map(etb).fillna(0)<.9).sum()),
          'R',round(g[g.symbol.map(etb).fillna(0)<.9].r.sum(),1))
    for L in (None,-2,-4):
        m=latch(g,L); gg=g.loc[m[m].index]
        c=card(gg); c['blocked']=int((~m).sum()); out[f'{k}|{L}']=c; print('latch',L,c)
    ge=g[g.symbol.map(etb).fillna(0)>=.9]; print('ETB-only no latch',card(ge))
    print('per-day R', g.groupby('date').r.sum().round(1).to_dict())
json.dump(out,open(W+'/live_cards.json','w'),indent=1,default=str)
