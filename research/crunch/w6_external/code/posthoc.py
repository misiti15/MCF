"""W6 post-hoc descriptives (labelled post hoc; counted as configs 27-30). Educational only - not financial advice.
usage: posthoc.py trades.pkl spy1m.pkl daily.parquet"""
import sys, numpy as np, pandas as pd
t=pd.read_pickle(sys.argv[1]); spy=pd.read_pickle(sys.argv[2]); daily=pd.read_parquet(sys.argv[3])
S=sorted(t.date.unique())
def tday(s): s=s.reindex(S,fill_value=0.0); return s.mean()/s.std(ddof=1)*np.sqrt(len(s))
# P1 gap relation
t=t[t.gap.notna()].copy(); t['gk']=np.where(t.gap.abs()<0.02,'no gap (<2%)',np.where(np.sign(t.gap)==t.side,'with gap','fade gap'))
print('== P1 trade R by relation to the open gap'); print(t.pivot_table(index='gk',columns='half',values='R',aggfunc=['mean','count']).round(3).to_string())
for a in ['primary']:
    x=t[t.acct==a]; print(a); print(x.pivot_table(index='gk',columns='half',values='R',aggfunc=['mean','count']).round(3).to_string())
per=t[t.gk=='fade gap'].groupby('strategy').R.agg(['count','mean','sum']).query('count>=20').sort_values('sum')
print(f'setups with >=20 gap-fade trades: {len(per)}; positive avg {int((per["mean"]>0).sum())}'); print(per.tail(5).round(3).to_string())
# P2 X5 reversed (late, against SPY first half hour)
spy['date']=spy.ts.dt.strftime('%Y-%m-%d'); spy['hm']=spy.ts.dt.hour*100+spy.ts.dt.minute
p10=spy[spy.hm<=959].groupby('date').c.last()
sd=daily[daily.symbol=='SPY'].copy(); sd['date']=sd.ts.dt.tz_convert('America/New_York').dt.strftime('%Y-%m-%d'); sd['pc']=sd.close.shift(1)
r30=p10/sd.set_index('date').pc.reindex(p10.index)-1
t['al']=np.sign(t.date.map(r30))==t.side
late=t[t.hhmm>=1500]; al=late[late.al]
d=-al.groupby('date').R.sum()
print(f'== P2 late (>=15:00) trades aligned with SPY 09:30-10:00 incl overnight: n {len(al)}, R {al.R.sum():+.1f}; skipping them: day-t {tday(d):.2f}, fit {-al[al.half=="fit"].R.sum():+.1f} check {-al[al.half=="check"].R.sum():+.1f}, days {al.date.nunique()}')
dd=al.groupby('date').R.sum().sort_values(); print('   worst days', dd.head(4).round(1).to_dict(), 'share of worst day', round(dd.iloc[0]/dd.sum(),2))
pr=al.groupby('strategy').R.agg(['count','sum']).sort_values('sum'); print('   by setup:', pr.head(6).round(1).to_dict('index'))
print('   by account:', late.groupby(['acct','al']).R.agg(['count','mean']).round(3).to_dict('index'))
# early window: against SPY direction before 10:00
ea=t[(t.hhmm<1000)&~t.al]
print(f'   early (<10:00) trades against SPY move-so-far: n {len(ea)}, avg {ea.R.mean():.3f}; fit {ea[ea.half=="fit"].R.mean():.3f} check {ea[ea.half=="check"].R.mean():.3f}; aligned early avg {t[(t.hhmm<1000)&t.al].R.mean():.3f}')
# P3 regime: R per trade by SPY rv10 tercile (pre-open)
q=t.drop_duplicates('date').rv10.quantile([1/3,2/3]).values
t['rvb']=pd.cut(t.rv10,[0,q[0],q[1],1],labels=['low','mid','high'])
print('== P3 R per trade by SPY prior-10-session realized vol tercile'); print(t.groupby(['rvb'],observed=False).agg(n=('R','size'),avg=('R','mean'),days=('date','nunique')).round(3).to_string())
print(t[t.acct=='primary'].groupby('rvb',observed=False).agg(n=('R','size'),avg=('R','mean'),dayR=('R',lambda x:x.sum()/max(1,t.loc[x.index,'date'].nunique()))).round(3).to_string())
print(t.groupby(['rvb','side'],observed=False).R.mean().unstack().round(3).to_string())
