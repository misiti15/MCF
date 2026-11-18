"""W6 post-hoc 3: open-flowsell (MF*) family vs open-gap fade, all accounts. Educational only - not financial advice. usage: posthoc3.py trades.pkl"""
import sys, numpy as np, pandas as pd
t=pd.read_pickle(sys.argv[1]); t=t[t.gap.notna()]; S=sorted(t.date.unique())
def tday(s): s=s.reindex(S,fill_value=0.0); return s.mean()/s.std(ddof=1)*np.sqrt(len(s))
t['fade']=(t.gap.abs()>=0.02)&(np.sign(t.gap)==-t.side)
f=t[t.strategy.str.match(r'^MF\d')]
print(f.pivot_table(index=['strategy'],columns=['fade','half'],values='R',aggfunc=['count','mean']).round(3).to_string())
for k,g in f.groupby('fade'): print(f'MF family fade={k}: n {len(g)} avg {g.R.mean():.3f} fit {g[g.half=="fit"].R.mean():.3f} check {g[g.half=="check"].R.mean():.3f}')
g=f[f.fade]; d=-g.groupby('date').R.sum(); dd=g.groupby('date').R.sum()
print(f'skip MF fades: R change {-g.R.sum():+.1f}, day-t {tday(d):.2f}, days {g.date.nunique()}, worst-day share {dd.min()/dd.sum():.2f}, improve {(g.groupby("strategy").R.sum()<0).sum()} / worsen {(g.groupby("strategy").R.sum()>0).sum()}')
print('fade side:', g.groupby('side').R.agg(['count','mean']).round(3).to_dict('index'))
print('gap size bucket:', g.assign(b=pd.cut(g.gap.abs(),[0.02,0.04,0.08,1])).groupby('b',observed=False).R.agg(['count','mean']).round(3).to_dict('index'))
