"""W4 extra checks: random-removal baseline for each chosen rule, and fit-vs-check stability of condition effects.
Educational only - not financial advice."""
import pandas as pd, numpy as np, math
exec(open('code/analyze.py').read().split("mapping=[]")[0])   # same data prep (setups, x, COND)
R=pd.read_csv('results.csv')
out=[]
rng=np.random.default_rng(20261118)
for r in R.itertuples():
    if not isinstance(r.rule,str) or r.rule.startswith('no rule'): continue
    d=x[(x.strategy==r.setup)&(~x.dup)].dropna(subset=['tod'])
    days=sorted(x[(x.strategy==r.setup)&(~x.dup)].date.unique()); half=days[:len(days)//2]
    chk=d[~d.date.isin(half)]
    if r.cond=='etf': rm=(chk.etf==r.thr)
    else: rm=((chk[r.cond]<r.thr) if r.tail=='low' else (chk[r.cond]>r.thr)).fillna(False)
    k=int(rm.sum()); 
    # random baseline: remove k random check trades, 2000 draws
    sims=np.array([-chk.R.values[rng.choice(len(chk),k,replace=False)].sum() for _ in range(2000)])
    real=-chk.R[rm].sum()
    # day-clustered excess: daily removed-R vs frac*day R
    frac=k/len(chk)
    dd=(-chk.R.where(rm,0)).groupby(chk.date).sum() - frac*(-chk.R.groupby(chk.date).sum())
    t=dd.mean()/(dd.std(ddof=1)/math.sqrt(len(dd))) if len(dd)>2 else np.nan
    out.append(dict(setup=r.setup,rule=r.rule,chk_removed=k,chk_gain=real,random_gain_mean=sims.mean(),excess=real-sims.mean(),pct_rank_vs_random=(sims<real).mean(),excess_t=t))
B=pd.DataFrame(out); B.to_csv('baseline.csv',index=False)
pd.set_option('display.width',250); print(B.round(2).to_string())
print('beat random:', (B.excess>0).sum(),'of',len(B), ' >=95th pct:',(B.pct_rank_vs_random>=0.95).sum())
# stability of condition effects: high-minus-low tercile avg R, fit vs check
st=[]
for s in setups:
    d=x[(x.strategy==s)&(~x.dup)].dropna(subset=['tod'])
    days=sorted(d.date.unique()); half=days[:len(days)//2]
    for c in COND:
        v=d.dropna(subset=[c])
        if len(v)<60: continue
        lo,hi=v[c].quantile([1/3,2/3])
        def sp(g): 
            a=g[g[c]<=lo].R.mean(); b=g[g[c]>=hi].R.mean(); return b-a
        f=v[v.date.isin(half)]; ch=v[~v.date.isin(half)]
        st.append(dict(setup=s,cond=c,fit_spread=sp(f),chk_spread=sp(ch)))
S=pd.DataFrame(st).dropna(); S.to_csv('stability.csv',index=False)
same=(np.sign(S.fit_spread)==np.sign(S.chk_spread)).mean()
print('pairs',len(S),'same sign',round(same,3),'corr',round(S.fit_spread.corr(S.chk_spread),3),'spearman',round(S.fit_spread.corr(S.chk_spread,method='spearman'),3))
big=S[S.fit_spread.abs()>=S.fit_spread.abs().quantile(0.75)]
print('top-quartile fit effects: n',len(big),'same sign',round((np.sign(big.fit_spread)==np.sign(big.chk_spread)).mean(),3),'chk/fit slope',round(np.polyfit(big.fit_spread,big.chk_spread,1)[0],3))
print(S.groupby('cond').apply(lambda g:pd.Series(dict(n=len(g),same=(np.sign(g.fit_spread)==np.sign(g.chk_spread)).mean(),corr=g.fit_spread.corr(g.chk_spread),mean_fit=g.fit_spread.mean(),mean_chk=g.chk_spread.mean()))).round(3))
