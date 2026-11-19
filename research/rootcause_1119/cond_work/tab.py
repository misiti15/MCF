import pandas as pd, numpy as np
def stats(g):
    n=len(g); R=g.R.sum()
    if n==0: return pd.Series(dict(n=0))
    dr=g.groupby("date").R.sum(); best=dr.idxmax()
    wo=g[g.date!=best]
    return pd.Series(dict(n=n,days=g.date.nunique(),avgR=round(g.R.mean(),3),totR=round(R,1),win=round((g.R>0).mean(),2),
        avg_wo_best=round(wo.R.mean(),3) if len(wo) else np.nan, best_share=round(dr.max()/R,2) if R>0 else np.nan))
def table(df,by):
    return df.groupby(by,observed=True).apply(stats,include_groups=False)
def cap3(A):
    A=A.sort_values(["setup","date","symbol","tod"]); A["k"]=A.groupby(["setup","date","symbol"]).cumcount(); return A[A.k<3]
