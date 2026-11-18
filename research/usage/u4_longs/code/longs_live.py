import sys; sys.path.insert(0,'.'); import jload, numpy as np, pandas as pd
t = jload.load(); L = t[t.side == 1]
MID = "2026-10-28"
def st(x):
    d = x.groupby("date").R.sum(); b = d.idxmax(); tot = d.sum()
    nb = (x.date == b).sum()
    f = x[x.date < MID].R; c = x[x.date >= MID].R
    dd = d.values; tcl = dd.mean() / (dd.std(ddof=1) / np.sqrt(len(dd))) if len(dd) > 2 and dd.std() > 0 else np.nan
    return pd.Series(dict(n=len(x), days=len(d), total=tot, avg=x.R.mean(), avg_wo_best=(tot - d.max()) / max(1, len(x) - nb),
        best_share=d.max() / tot if tot > 0 else np.nan, fit_avg=f.mean(), fit_n=len(f), chk_avg=c.mean(), chk_n=len(c), t_day=tcl,
        accts=",".join(sorted(x.acct.unique()))))
g = L.groupby("strategy").apply(st)
g.to_csv(f"{jload.S}/longs_live.csv")
pd.set_option("display.width", 250); pd.set_option("display.max_rows", 300)
print(len(g), "long setups;", "total", L.R.sum(), "n", len(L))
q = g[(g.n >= 30)].sort_values("avg_wo_best", ascending=False)
print(q.head(40).round(3).to_string())
print("positive in both halves w/ n>=30, avg_wo_best>0:")
print(q[(q.fit_avg > 0) & (q.chk_avg > 0) & (q.avg_wo_best > 0)].round(3).to_string())
