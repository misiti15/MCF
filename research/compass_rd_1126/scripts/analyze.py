"""Conditional map on live trades: per setup (>= 30 trades) avg R by condition at entry; shrinkage k=20 toward the setup
mean; aligned contrasts with day-clustered t. Educational only - not financial advice."""
import sys, numpy as np, pandas as pd
D = "/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/crd/"
K = 20
t = pd.read_parquet(D + "live_feat.parquet")
side = t.expo.values
t["cmp_al"] = side * t.cmp
bins = [-np.inf, -0.005, -0.001, 0.001, 0.005, np.inf]; lab = ["<-0.5", "-0.5..-0.1", "flat", "+0.1..+0.5", ">+0.5"]
t["spyb"] = pd.cut(t.spy_fo, bins, labels=lab).astype(str)
# aligned: +1 = condition is on the trade's side (SPY up for a long, down for a short)
t["spyo_al"] = side * np.where(t.spy_fo > .001, 1, np.where(t.spy_fo < -.001, -1, 0))
t["idx3_al"] = side * t.idx3
t["gap_al"] = side * t.gapst
t["day_al"] = side * np.where(t.dtype.isin(["up", "V-up"]), 1, np.where(t.dtype.isin(["down", "V-down"]), -1, 0))
FAM = {"spyb": lab, "dtype": ["up", "down", "flat", "V-up", "V-down"], "idx3_al": [1, 0, -1], "gap_al": [1, 0, -1], "spyo_al": [1, 0, -1], "day_al": [1, 0, -1]}
FAM["cmp_al"] = [1, 0, -1]; FAM["cmp_after"] = [0, 1]

def cl_mean(r, d):
    n = len(r)
    if n < 2: return np.nan, np.nan
    m = r.mean(); e = pd.Series(r - m).groupby(d).sum().values
    return m, np.sqrt((e ** 2).sum()) / n

rows, cells = [], 0
for s, g in t.groupby("strategy"):
    if len(g) < 30: continue
    mu = g.r.mean()
    rec = dict(setup=s, side=int(g.side.iloc[0]), n=len(g), days=g.date.nunique(), avg=mu, tot=g.r.sum())
    for f, levels in FAM.items():
        for L in levels:
            x = g[g[f] == L]; cells += 1
            rec[f"{f}={L}:n"] = len(x)
            rec[f"{f}={L}:avg"] = x.r.mean() if len(x) else np.nan
            rec[f"{f}={L}:shr"] = (x.r.sum() + K * mu) / (len(x) + K)
        if f.endswith("_al") or f == "cmp_after":
            a, b = (g[g[f] == 1], g[g[f] == -1]) if f != "cmp_after" else (g[g[f] == 1], g[g[f] == 0])
            if len(a) >= 10 and len(b) >= 10:
                ma, sa = cl_mean(a.r.values, a.date.values); mb, sb = cl_mean(b.r.values, b.date.values)
                rec[f"{f}:diff"] = ma - mb; rec[f"{f}:t"] = (ma - mb) / np.sqrt(sa ** 2 + sb ** 2)
                rec[f"{f}:wdays"] = a.date.nunique(); rec[f"{f}:adays"] = b.date.nunique()
                sha, shb = rec[f"{f}=1:shr"], rec[f"{f}=-1:shr" if f != "cmp_after" else f"{f}=0:shr"]
                rec[f"{f}:flip"] = bool(np.sign(sha) != np.sign(shb))
    rows.append(rec)
R = pd.DataFrame(rows); R.to_csv(D + "cond_live.csv", index=False)
print("setups", len(R), "cells", cells)
