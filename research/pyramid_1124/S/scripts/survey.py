import pandas as pd, numpy as np, sys
W=sys.argv[1]; t=pd.read_pickle(W+'/all.pkl'); t=t[~t.dup]
days=sorted(t.date.unique())
book=t[t.account=='primary'].groupby('date').r.sum().reindex(days,fill_value=0)
worst10=book.nsmallest(10).index
print('primary book total',round(book.sum(),1),'worst10',book.nsmallest(10).round(1).to_dict())
rows=[]
for s,g in t[t.side==-1].groupby('strategy'):
    if len(g)<20: continue
    d=g.groupby('date').r.sum(); tot=d.sum(); b=d.idxmax()
    dd=d.reindex(days,fill_value=0)
    # t-stat day clustered
    tday=d.mean()/(d.std(ddof=1)/np.sqrt(len(d))) if len(d)>2 else np.nan
    rows.append(dict(s=s[:60],n=len(g),ses=len(d),first=g.date.min(),avg=g.r.mean(),wo=g[g.date!=b].r.mean(),share=d.max()/tot if tot>0 else np.nan,
      tot=tot,tday=tday,corr=np.corrcoef(dd,book)[0,1],w10=dd[worst10].sum(),acct=','.join(sorted(g.account.unique()))))
x=pd.DataFrame(rows).sort_values('tot',ascending=False)
pd.set_option('display.width',300); pd.set_option('display.max_colwidth',60)
print(x[(x.tot>5)].round(3).to_string(index=False))
