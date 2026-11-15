# Sizing-up study 2026-11-15 (run from the repo root). Educational only - not financial advice.
import sys,json;sys.path.insert(0,'research/sizing_1115')
import pandas as pd,numpy as np
from load import load
t=load()
A=json.load(open('docs/live/assignments.json'))['accounts']; T6=A['primary']
b=t[t.strategy.isin(T6)].copy()
# $ per base R in Primary for each setup: median risk$ of its Primary trades on TEAM-6 days (11-11..13)
p6=t[(t.acct=='primary')&(t.date>='2026-11-11')]
rd=p6.groupby('strategy').risk.mean().to_dict(); print({k[:10]:round(v,1) for k,v in rd.items()})
b['usd']=b.R*b.strategy.map(rd)
day=b.groupby('date').agg(R=('R','sum'),usd=('usd','sum'))
ses=b.groupby(['strategy','date']).R.sum().unstack(0).fillna(0)
sesu=b.groupby(['strategy','date']).usd.sum().unstack(0).fillna(0)
print('pro-forma T6 book days',len(day),'avgR %.2f worst %.2f  avg$ %.0f worst$ %.0f'%(day.R.mean(),day.R.min(),day.usd.mean(),day.usd.min()))
cfgs={'A (strict): NM-ETF':['NM-ETF-late-dip-di-long'],'B (loose): NM-ETF+ST7':['NM-ETF-late-dip-di-long','ST7-rsi50dn-long-pm-t1s1-FD']}
for name,S in cfgs.items():
  for m in (1.05,1.10,1.15):
    d=day.R+sum((m-1)*ses[s] for s in S); du=day.usd+sum((m-1)*sesu[s] for s in S)
    imp=[(s,(ses[s]>0).sum(),(ses[s]<0).sum(),(m-1)*ses[s][ses[s]>0].sum(),(m-1)*ses[s][ses[s]<0].sum(),(m-1)*ses[s].min()) for s in S]
    print(f'{name} x{m}: avgR {d.mean():.3f} (+{d.mean()-day.R.mean():.3f}) worst {d.min():.2f} avg$ {du.mean():.0f} (+{du.mean()-day.usd.mean():.1f}) worst$ {du.min():.0f}; days<=-15R {(d<=-15).sum()}')
    for s,g,r,gain,loss,w in imp: print(f'   {s[:14]}: green ses {g} gain {gain:+.2f}R  red ses {r} loss {loss:+.2f}R  worst-ses extra {w:+.2f}R')
# BP: peak concurrent notional in Primary per day on TEAM-6 days
for dt,g in p6.groupby('date'):
    ev=[(pd.Timestamp(r.entry_time),r.notional,r.strategy) for r in g.itertuples()]+[(pd.Timestamp(r.exit_time),-r.notional,r.strategy) for r in g.itertuples()]
    ev.sort(key=lambda x:x[0]); cur=0;pk=0;nm=0;pknm=0;cnt=0;pkc=0
    for ts,v,s in ev:
        cur+=v; cnt+=1 if v>0 else -1
        if 'NM-ETF' in s or 'ST7' in s: nm+=v
        if cur>pk: pk=cur;pknm=nm;pkc=cnt
    print(dt,'peak open notional $%.0f (%d lots), of which NM-ETF+ST7 $%.0f; +15%% adds $%.0f'%(pk,pkc,pknm,0.15*pknm))
nmmax=p6[p6.strategy.str.contains('NM-ETF|ST7')].notional.max(); print('max single NM/ST7 notional',nmmax)
