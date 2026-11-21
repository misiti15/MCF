import sys; sys.argv=['x','w','none']
import pandas as pd, numpy as np
exec(open('nb.py').read().split('if __name__ == "__main__":')[0])
etb=pd.read_parquet('etb_rate.parquet').rate
T=add_r(pd.read_parquet('w/trades_t1.parquet'))
lv=pd.read_pickle('../promo-pipe/live.pkl')
for v,c in (('P1-base','L3-gap-slope-lowdist-FD'),('P4-base','CWT09-gapdn-vwaploss-g10-short')):
    b=book(T[T.setup==v],BOOK['testing'],etb); b=b[(b.date>='2026-10-13')&(b.date<='2026-11-04')]
    l=lv[(lv.strategy==c)&(lv.date<='2026-11-04')]
    ks=set(zip(b.symbol,b.date)); kl=set(zip(l.symbol,l.date))
    both=ks&kl
    print(v,'lab',len(b),round(b.r.mean(),3),round(b.r.sum(),1),'| live',len(l),round(l.r.mean(),3),round(l.r.sum(),1),'| symbol-days lab',len(ks),'live',len(kl),'shared',len(both))
    lb=b[[k in both for k in zip(b.symbol,b.date)]]; ll=l[[k in both for k in zip(l.symbol,l.date)]]
    print('   shared: lab avg',round(lb.r.mean(),3),'live avg',round(ll.r.mean(),3), ' lab-only avg', round(b[[k not in kl for k in zip(b.symbol,b.date)]].r.mean(),3),' live-only avg',round(l[[k not in ks for k in zip(l.symbol,l.date)]].r.mean(),3))
b=book(T[T.setup=='P1-base'],BOOK['testing'],etb); b=b[(b.date>='2026-10-13')&(b.date<='2026-11-04')]
l=lv[(lv.strategy=='L3-gap-slope-lowdist-FD')&(lv.date<='2026-11-04')]
kl=set(zip(l.symbol,l.date)); b['shared']=[k in kl for k in zip(b.symbol,b.date)]
b['riskpct']=b.risk/b.entry*100
print(b.groupby('shared')[['entry','riskpct','tod','gap','stop_cost_r','r']].median())
print(b.groupby('shared').size())
allsym=set(lv.symbol)
b['live_univ']=b.symbol.isin(allsym); print(pd.crosstab(b.shared,b.live_univ))
print(b[~b.shared].groupby('date').size().head(20)); print(l.groupby('date').size())
