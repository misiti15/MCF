"""W6 post-hoc 2: SPY move-so-far at entry (no look-ahead) and Primary gap-fade breakdown. Educational only - not financial advice.
usage: posthoc2.py trades.pkl spy1m.pkl daily.parquet"""
import sys, numpy as np, pandas as pd
t=pd.read_pickle(sys.argv[1]); spy=pd.read_pickle(sys.argv[2]); daily=pd.read_parquet(sys.argv[3])
S=sorted(t.date.unique())
def tday(s): s=s.reindex(S,fill_value=0.0); return s.mean()/s.std(ddof=1)*np.sqrt(len(s))
def wobd(r,dates):
    dd=r.groupby(dates).sum(); b=dd.idxmax(); n=(dates!=b).sum(); return (dd.sum()-dd.max())/n, dd.max()/dd.sum() if dd.sum()>0 else float('nan')
sd=daily[daily.symbol=='SPY'].copy(); sd['date']=sd.ts.dt.tz_convert('America/New_York').dt.strftime('%Y-%m-%d'); sd['pc']=sd.close.shift(1)
spy=spy.sort_values('ts'); spy['tsm']=spy.ts+pd.Timedelta(minutes=1)   # bar close time
x=t.sort_values('et').copy(); x['etn']=x.et.dt.tz_convert('America/New_York')
m=pd.merge_asof(x,spy[['tsm','c']].rename(columns={'tsm':'etn'}),on='etn',direction='backward')
m['spy_sofar']=m.c/m.date.map(sd.set_index('date').pc)-1
m['al']=np.sign(m.spy_sofar)==m.side
m['win']=pd.cut(m.hhmm,[0,1000,1130,1400,1500,1600],labels=['<10','10-11:30','11:30-14','14-15','>=15'])
print('== Q1 R by entry window x aligned with SPY move since prior close at entry (no look-ahead)')
print(m.pivot_table(index='win',columns=['al','half'],values='R',aggfunc='mean',observed=False).round(3).to_string())
print(m.pivot_table(index='win',columns='al',values='R',aggfunc='count',observed=False).to_string())
for w in ['<10','>=15']:
    g=m[(m.win==w)&(~m.al if w=='<10' else m.al)]; d=-g.groupby('date').R.sum()
    print(f' skip {"against" if w=="<10" else "aligned"} in {w}: n {len(g)}, R change {-g.R.sum():+.1f} (fit {-g[g.half=="fit"].R.sum():+.1f}, check {-g[g.half=="check"].R.sum():+.1f}), day-t {tday(d):.2f}, setups improve {(g.groupby("strategy").R.sum()<0).sum()} / worsen {(g.groupby("strategy").R.sum()>0).sum()}')
    pa=g[g.acct=='primary']; print(f'   in Primary: n {len(pa)}, R {pa.R.sum():+.1f}')
print('== Q2 Primary gap-fade trades (abs gap >= 2%, side against the gap) by setup')
p=t[(t.acct=='primary')]; p=p.assign(fade=(p.gap.abs()>=0.02)&(np.sign(p.gap)==-p.side))
g=p[p.fade]; print(f'n {len(g)}, R {g.R.sum():+.1f}, fit {g[g.half=="fit"].R.sum():+.1f}, check {g[g.half=="check"].R.sum():+.1f}, day-t of skipping {tday(-g.groupby("date").R.sum()):.2f}, days {g.date.nunique()}')
a,sh=wobd(-g.R,g.date); print(f' avg R saved per skipped trade w/o best day {a:+.3f}, best-day share {sh:.2f}')
print(p.groupby(['strategy','fade']).R.agg(['count','mean','sum']).round(3).to_string())
print('== Q3 same split, all accounts, setups with >=10 fade and >=10 non-fade trades: fade avg vs rest avg')
t['fade']=(t.gap.abs()>=0.02)&(np.sign(t.gap)==-t.side)
z=t.groupby(['strategy','fade']).R.agg(['count','mean']).unstack()
z=z[(z[('count',True)]>=10)&(z[('count',False)]>=10)]
dlt=z[('mean',True)]-z[('mean',False)]
print(f'setups {len(z)}: fade worse in {(dlt<0).sum()}, better in {(dlt>0).sum()}, median delta {dlt.median():+.3f}R')
# by family prefix of setups whose own definition is a gap fade vs not
t['fam']=t.strategy.str.extract(r'^([A-Za-z]+\d*)')[0]
print(t[t.fade].groupby('fam').R.agg(['count','mean','sum']).query('count>=40').sort_values('sum').round(3).to_string())
print('== Q4 early (<10:00) trades against SPY move-so-far: concentration and setups')
g=m[(m.win=='<10')&~m.al]; h=m[(m.win=='<10')&m.al]
a,sh=wobd(-g.R,g.date); print(f'avg R saved per skipped trade w/o best day {a:+.3f}, best-day share {sh:.2f}, days {g.date.nunique()}')
dd=g.groupby('date').R.sum().sort_values(); print(' worst days', dd.head(5).round(1).to_dict())
print(' by side:', g.groupby('side').R.agg(['count','mean']).round(3).to_dict('index'), 'aligned by side:', h.groupby('side').R.agg(['count','mean']).round(3).to_dict('index'))
ps=g.groupby('strategy').R.agg(['count','mean','sum']); pa=h.groupby('strategy').R.agg(['count','mean'])
j=ps.join(pa,rsuffix='_al').query('count>=10').sort_values('sum'); print(j.round(3).head(12).to_string()); print(j.round(3).tail(6).to_string())
for s in ['L3-gap-slope-fromopen-FD','RW3-gapdn-rsi5pop-flowsell-short-FD','RW5-heat30-flowsell-rsi5pop-gapdn-short-FD','MF2-open-rsimidhi-flowsell-FD','MF4-h40-open-flowsell-FD','ST7-rsi50dn-long-pm-t1s1-FD','NM-ETF-late-dip-di-long']:
    x=m[(m.strategy==s)&(m.win=='<10')]; print(f' {s}: early n {len(x)}, against n {(~x.al).sum()} avg {x[~x.al].R.mean():.3f}, aligned avg {x[x.al].R.mean():.3f}')
# by |SPY move so far| size
g2=m[m.win=='<10'].copy(); g2['mag']=pd.cut(g2.spy_sofar.abs(),[0,0.002,0.005,1],labels=['<0.2%','0.2-0.5%','>0.5%'])
print(g2.pivot_table(index='mag',columns='al',values='R',aggfunc=['mean','count'],observed=False).round(3).to_string())
print('== Q5 early-against excluding CWT12/CWT14 families (closed to new variants)')
e=m[(m.win=='<10')&~m.strategy.str.startswith(('CWT12','CWT14'))]
for k,gg in e.groupby('al'): print(f' aligned={k}: n {len(gg)} avg {gg.R.mean():.3f} fit {gg[gg.half=="fit"].R.mean():.3f} check {gg[gg.half=="check"].R.mean():.3f}')
g=e[~e.al]; print(f' skip against: R change {-g.R.sum():+.1f}, day-t {tday(-g.groupby("date").R.sum()):.2f}, improve {(g.groupby("strategy").R.sum()<0).sum()} / worsen {(g.groupby("strategy").R.sum()>0).sum()}')
