"""OBS-FILLCLOCK part 2 (Observer 11-11 late): where the decision->fill time goes, and does it cost R? Live journals 10-20..11-11,
submitted signals joined to orders + trades. lag = orders.created_at - signals.ts; drift = side*(fill - ref_price)/|ref_price - stop| (R vs the
decision price; |drift|<2 guard). Slope of drift on lag with day-clustered SE. 0 configs. Educational only - not financial advice.
usage: python lagcost.py <dir of journals>"""
import sqlite3,pandas as pd,numpy as np,sys
D=sys.argv[1]; out=[]
for nm,b in [('Primary','mcf-data'),('On Deck','mcf-data-testing'),('Testing A','mcf-data-testing2'),('Graveyard','mcf-data-graveyard'),('Gen','mcf-data-gen')]:
  c=sqlite3.connect(f'{D}/{b}.db')
  t=pd.read_sql("select t.date,t.side tside,t.entry,t.stop tstop,s.side,s.ref_price,s.stop,s.ts,o.created_at from trades t join signals s on s.broker_order_id=t.broker_order_id join orders o on o.broker_order_id=t.broker_order_id where t.run_id=1 and t.date between '2026-10-20' and '2026-11-11' and s.status='submitted'",c)
  t['lag']=(pd.to_datetime(t.created_at,utc=True,format='mixed')-pd.to_datetime(t.ts,utc=True)).dt.total_seconds()
  risk=(t.ref_price-t.stop).abs(); t=t[risk>0]
  t['drift']=t.side*(t.entry-t.ref_price)/(t.ref_price-t.stop).abs()
  t=t[t.drift.abs()<2]   # guard: split/bad rows
  t['day']=t.date
  b_=pd.cut(t.lag,[-1,20,40,80,1e9],labels=['<20s','20-40','40-80','>80'])
  g=t.groupby(b_,observed=True).drift.agg(['count','mean'])
  # day-clustered t for slope of drift on lag (per minute)
  x=t.lag/60; X=np.c_[np.ones(len(t)),x]; beta=np.linalg.lstsq(X,t.drift,rcond=None)[0]
  r=t.drift-X@beta; XtXi=np.linalg.inv(X.T@X)
  meat=sum(np.outer(X[i].T@r.values[i],X[i].T@r.values[i]) for i in [np.where(t.day.values==d)[0] for d in t.day.unique()])
  se=np.sqrt(np.diag(XtXi@meat@XtXi))
  print(f"{nm:10s} n {len(t):5d} days {t.day.nunique()} lag med {t.lag.median():.0f}s  mean drift {t.drift.mean():+.4f}R  slope {beta[1]:+.4f}R/min (day-t {beta[1]/se[1]:+.2f})  by lag:",
        {k:(int(v['count']),round(v['mean'],4)) for k,v in g.iterrows()})
