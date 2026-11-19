import pandas as pd, numpy as np
t=pd.read_parquet('merged.parquet')
t['stop_bps']=(t.entry-t.stop).abs()/t.entry*1e4
t['cost']=t.r_raw-t.R
t['stop_atr']=(t.entry-t.stop).abs()/(t.atr_pct/100*t.entry)
def s(g):
    dr=g.groupby('date').R.sum(); tot=g.R.sum()
    return pd.Series(dict(n=len(g),setups=g.base.nunique(),avg=g.R.mean(),avg_wo=(tot-dr.max())/max((g.date!=dr.idxmax()).sum(),1),bshare=dr.max()/tot if tot>0 else np.nan,
      h1=g[g.half=='H1'].R.mean(),h2=g[g.half=='H2'].R.mean(),n1=(g.half=='H1').sum(),n2=(g.half=='H2').sum(),raw=g.r_raw.mean(),cost=g.cost.mean(),daysT=dr.mean()/(dr.std()/np.sqrt(len(dr))) if len(dr)>2 else np.nan))
pd.set_option('display.width',250)
print('cost by stop_bps'); print(t.groupby(pd.qcut(t.stop_bps,8),observed=True).apply(s).round(3).to_string())
print('stop in ATR'); print(t.groupby(pd.qcut(t.stop_atr,6),observed=True).apply(s).round(3).to_string())
print('cost pre/post 11-12', t.groupby(t.date>='2026-11-12').cost.mean().round(3).to_dict())
sh=t[t.side<0]; lg=t[t.side>0]
cells={
 'short gap<=-1.5':sh.gap_pct<=-1.5,
 'short gap>=+0.5':sh.gap_pct>=0.5,
 'short dsma20<-5':sh.dsma20<-5,
 'short rsi5>=65':sh.rsi5>=65,
 'short rsi5<25':sh.rsi5<25,
 'short tod>=11:00':sh.tod>=660,
 'short gap<=-1.5 & rsi5>=65':(sh.gap_pct<=-1.5)&(sh.rsi5>=65),
 'short gap<=-1.5 & fo>0 (bounced)':(sh.gap_pct<=-1.5)&(sh.fo_atr>0),
 'short gap<=-1.5 & dsma20<0 & rsi5>=60':(sh.gap_pct<=-1.5)&(sh.dsma20<0)&(sh.rsi5>=60),
 'short gap<=-1.5 & rsi5>=60 & tod>=11:00':(sh.gap_pct<=-1.5)&(sh.rsi5>=60)&(sh.tod>=660),
 'short gap<=-1.5 & rsi5>=60 & tod>=11:00 & atr%>=3':(sh.gap_pct<=-1.5)&(sh.rsi5>=60)&(sh.tod>=660)&(sh.atr_pct>=3),
 'short dsma20<-5 & rsi5>=65 & tod>=11':(sh.dsma20<-5)&(sh.rsi5>=65)&(sh.tod>=660),
 'short excl gap-up & excl rsi5<25':(sh.gap_pct<0.5)&(sh.rsi5>=25),
}
rows=[]
for k,m in cells.items():
    rows.append(s(sh[m]).rename(k))
cl={
 'long gap>=+3':lg.gap_pct>=3,
 'long tod>=14:30':lg.tod>=870,
 'long tod 10:30-11:30':(lg.tod>=630)&(lg.tod<690),
 'long etf':lg.etf==True,
 'long spy_fo>=0.3':lg.spy_fo>=0.3,
 'long spy_fo in(-0.75,-0.3)':(lg.spy_fo>-0.75)&(lg.spy_fo<-0.3),
 'long rsi5<15':lg.rsi5<15,
 'long atr%>=5':lg.atr_pct>=5,
 'long atr%>=5 & spy_fo>0':(lg.atr_pct>=5)&(lg.spy_fo>0),
 'long tod>=14:30 & spy_fo>0':(lg.tod>=870)&(lg.spy_fo>0),
 'long rvol15<0.5':lg.rvol15<0.5,
}
for k,m in cl.items(): rows.append(s(lg[m]).rename(k))
for k,m in {'all atr%>=5':t.atr_pct>=5,'all atr%<2.3':t.atr_pct<2.3,'all rvol15>1.36':t.rvol15>1.36,'all stop_bps>=150':t.stop_bps>=150,'all stop_bps<60':t.stop_bps<60,'all tod<10:30':t.tod<630,'all tod 14:30-15:00':(t.tod>=870)&(t.tod<900)}.items():
    rows.append(s(t[m]).rename(k))
R=pd.DataFrame(rows); print(R.round(3).to_string())
R.to_csv('cells.csv')
# top cell by base setup
m=(sh.gap_pct<=-1.5)&(sh.rsi5>=60)&(sh.tod>=660)
print(sh[m].groupby('base').apply(lambda g: pd.Series(dict(n=len(g),avg=g.R.mean(),tot=g.R.sum()))).sort_values('n',ascending=False).head(25).round(3).to_string())
m2=(sh.gap_pct>=0.5)
x=sh[m2].groupby('fam').apply(lambda g: pd.Series(dict(n=len(g),avg=g.R.mean(),avg_all=sh[sh.fam==g.name].R.mean()))).sort_values('n',ascending=False).head(20)
print('gap-up shorts by family (vs that family all shorts)'); print(x.round(3).to_string())
print('families improved by dropping gap-up shorts:', (x.avg<x.avg_all).sum(), 'of', len(x))
