import pandas as pd, numpy as np
t=pd.read_pickle('live.pkl')
LU=['L3-gap-slope-fromopen-FD','RW3-gapdn-rsi5pop-flowsell-short-FD','RW5-heat30-flowsell-rsi5pop-gapdn-short-FD','NM-ETF-late-dip-di-long','ST7-rsi50dn-long-pm-t1s1-FD']
C=['RW7-gapdn-bounce-early-short-FD','L3-gap-slope-lowdist-FD','L3-gap-slope-rsi5hi-FD','RW1-gapdn-bounce-flowsell-short-FD','CWT09-gapdn-vwaploss-g10-short','GEN-261029-06','GEN-261026-07','RW6-ns2-up3-short-FD','GEN-261020-09']
def pick(c): return t[t.strategy.str.startswith(c)]
days=sorted(t.date.unique())
lu=t[t.strategy.isin(LU)]
L=lu.groupby('date').r.sum().reindex(days,fill_value=0)
# restrict to dates where lineup traded at all (from 10-13)
P=t[t.account=='primary'].groupby('date').r.sum().reindex(days,fill_value=0)
print('lineup pooled: tot %.1f green %d/%d'%(L.sum(),(L>0).sum(),len(L)))
rows=[]
for c in C:
    x=pick(c); d=x.groupby('date').r.sum().reindex(days,fill_value=0)
    m=np.array(days)>=x.date.min()
    for nm,B in (('lineup',L),('primaryacct',P)):
        red=(B<0)&m; green=(B>0)&m
        comb=B+d
        rows.append(dict(cand=c[:34],base=nm,days=int(m.sum()),corr=round(np.corrcoef(d[m],B[m])[0,1],2),
          R_red=round(d[red].sum(),1),n_red=int(red.sum()),cand_green_on_red=int((d[red]>0).sum()),
          flips=int(((B<0)&(comb>0)&m).sum()),R_green=round(d[green].sum(),1),
          base_green=int((B[m]>0).sum()),comb_green=int((comb[m]>0).sum()),
          base_worst=round(B[m].min(),1),comb_worst=round(comb[m].min(),1),
          base_med=round(B[m].median(),2),comb_med=round(comb[m].median(),2)))
pd.set_option('display.width',250)
print(pd.DataFrame(rows).to_string(index=False))
