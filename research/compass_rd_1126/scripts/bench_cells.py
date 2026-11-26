"""Cells + aligned contrasts per setup x split on the tagged bench trades. Educational only - not financial advice."""
import numpy as np, pandas as pd
W = "/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/crd/bench/"
t = pd.read_parquet(W + "bench_tagged.parquet")
FAM = {"spyb": ["<-0.5", "-0.5..-0.1", "flat", "+0.1..+0.5", ">+0.5"], "dtype": ["up", "down", "flat", "V-up", "V-down"],
       "idx3_al": [1, 0, -1], "gap_al": [1, 0, -1], "spyo_al": [1, 0, -1], "cp30_al": [1, 0, -1], "day_al": [1, 0, -1]}
def cl(r, d):
    m = r.mean(); e = pd.Series(r - m).groupby(d).sum().values; return m, np.sqrt((e ** 2).sum()) / len(r)
rows, cells = [], 0
for (s, sp), g in t.groupby(["setup", "split"]):
    mu = g.r.mean(); rec = dict(setup=s, split=sp, n=len(g), days=g.date.nunique(), avg=mu)
    for f, L in FAM.items():
        for v in L:
            x = g[g[f] == v]; cells += 1
            rec[f"{f}={v}:n"] = len(x); rec[f"{f}={v}:avg"] = x.r.mean() if len(x) else np.nan
        if f.endswith("_al"):
            a, b = g[g[f] == 1], g[g[f] == -1]
            if len(a) >= 10 and len(b) >= 10:
                ma, sa = cl(a.r.values, a.date.values); mb, sb = cl(b.r.values, b.date.values)
                rec[f"{f}:diff"] = ma - mb; rec[f"{f}:t"] = (ma - mb) / np.sqrt(sa ** 2 + sb ** 2)
    rows.append(rec)
R = pd.DataFrame(rows); R.to_csv(W + "bench_cells.csv", index=False); print("cells", cells)
pd.set_option("display.width", 250)
for f in ["spyo_al", "idx3_al", "gap_al", "cp30_al", "day_al"]:
    p = R.pivot(index="setup", columns="split", values=f + ":diff").round(3); q = R.pivot(index="setup", columns="split", values=f + ":t").round(2)
    print("==", f, "diff (with - against) / t"); print(pd.concat([p, q], axis=1, keys=["diff", "t"]).to_string())
