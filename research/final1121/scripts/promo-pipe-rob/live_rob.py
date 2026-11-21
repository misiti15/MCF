import pandas as pd, numpy as np, math
t=pd.read_pickle('../promo-pipe/live.pkl')
risk=(t.entry-t.stop).abs()*t.shares.abs()
t['gross']=t.pnl/risk; t['cost']=t.gross-t.r
LU=['L3-gap-slope-fromopen-FD','RW3-gapdn-rsi5pop-flowsell-short-FD','RW5-heat30-flowsell-rsi5pop-gapdn-short-FD','NM-ETF-late-dip-di-long','ST7-rsi50dn-long-pm-t1s1-FD']
days=sorted(t.date.unique())
P=t[t.account=='primary'].groupby('date').r.sum().reindex(days,fill_value=0)
L=t[t.strategy.isin(LU)].groupby('date').r.sum().reindex(days,fill_value=0)
def ct(x,col='r'):
    m=x[col].mean(); e=(x[col]-m).groupby(x.date).sum(); G=e.size
    se=math.sqrt((e**2).sum()*G/(G-1))/len(x); return m/se
def rec(x,col='r'):
    if len(x)<2: return dict(n=len(x))
    d=x.groupby('date')[col].sum(); s=d.sort_values(ascending=False); tot=x[col].sum(); n=len(x)
    return dict(n=n,sess=d.size,tot=round(tot,1),avg=round(x[col].mean(),3),
      wo1=round(x[~x.date.isin(s.index[:1])][col].mean(),3) if d.size>1 else None,
      wo2=round(x[~x.date.isin(s.index[:2])][col].mean(),3) if d.size>2 else None,
      bshare=round(s.iloc[0]/tot,2) if tot>0 else None, t_cl=round(ct(x,col),2) if d.size>2 else None,
      green=round((d>0).mean(),2), worst=round(d.min(),1))
pd.set_option('display.width',250)
for c in ['L3-gap-slope-lowdist-FD','CWT09-gapdn-vwaploss-g10-short']:
    x=t[t.strategy==c].copy(); x['r50']=x.r-0.5*x.cost; x['r100']=x.r-x.cost
    rows=[]
    rows.append(dict(view='all',**rec(x)))
    rows.append(dict(view='gross (no cost)',**rec(x,'gross')))
    rows.append(dict(view='cost +50%',**rec(x,'r50')))
    rows.append(dict(view='cost +100%',**rec(x,'r100')))
    # calendar halves of the setup's live window
    span=[d for d in days if d>=x.date.min()]; h=span[len(span)//2]
    rows.append(dict(view=f'half1 <{h[5:]}',**rec(x[x.date<h]))); rows.append(dict(view=f'half2 >={h[5:]}',**rec(x[x.date>=h])))
    for mth,g in x.groupby(x.date.str[:7]): rows.append(dict(view='month '+mth,**rec(g)))
    for a,g in x.groupby('account'): rows.append(dict(view='acct '+a,**rec(g)))
    # entry-time buckets
    et=pd.to_datetime(x.entry_time,utc=True,format='mixed').dt.tz_convert('America/New_York')
    hh=et.dt.hour*100+et.dt.minute
    for nm,m in (('entry<11:00',hh<1100),('11:00-13:00',(hh>=1100)&(hh<1300)),('>=13:00',hh>=1300)): rows.append(dict(view=nm,**rec(x[m.values])))
    # symbol concentration
    sy=x.groupby('symbol').r.sum().sort_values(ascending=False)
    rows.append(dict(view=f'w/o top symbol {sy.index[0]}',**rec(x[x.symbol!=sy.index[0]])))
    print('=====',c,'avg cost R/trade %.3f'%x.cost.mean()); print(pd.DataFrame(rows).to_string(index=False))
    d=x.groupby('date').r.sum().reindex(days,fill_value=0); m=np.array(days)>=x.date.min()
    for nm,B in (('Primary acct',P),('current five pooled',L)):
        red=(B<0)&m; comb=B+d
        print(f'  corr vs {nm}: {np.corrcoef(d[m],B[m])[0,1]:+.2f}; on its {int(red.sum())} red days {d[red].sum():+.1f}R, green {int((d[red]>0).sum())}, flips red->green {int(((B<0)&(comb>0)&m).sum())}; on green days {d[(B>0)&m].sum():+.1f}R')
    # daily-sum t
    dd=x.groupby('date').r.sum(); print('  daily-sum t (traded days) %.2f'%(dd.mean()/dd.std()*math.sqrt(dd.size)))
