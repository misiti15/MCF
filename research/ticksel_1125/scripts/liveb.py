"""Live ticker test without overlap: lab ranks from FIT + CHECK up to 2026-10-05 only (live starts 10-06). Educational only."""
import sys, json
import numpy as np, pandas as pd
sys.path.insert(0, "/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/ticksel")
from lib2 import *
from prep import FAM
S = "/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/"; T = S + "ticksel/"
L = pd.read_parquet(S + "pyramid/X/live_dedup.parquet"); L = L[L.strategy.isin(FAM)].rename(columns={"strategy": "setup"})
L["date"] = L.date.astype(str)
B = pd.read_parquet(T + "bk_t1.parquet"); B = B[~B.rnd & B.half.isin(["fit", "check"])]
out = []
for cut in ("2026-10-05", "2026-11-04"):
    b = B[B.date <= cut]; rows = []
    for s, f in b.groupby("setup"):
        mu = f.r.mean(); g = f.groupby("symbol").r.agg(["size", "mean"])
        g["shr"] = (g["size"] * g["mean"] + 20 * mu) / (g["size"] + 20); q = g[g["size"] >= 3]
        top, bot = set(q.index[q.shr >= q.shr.quantile(.9)]), set(q.index[q.shr <= q.shr.quantile(.1)])
        G = L[L.setup == s].copy()
        G["grp"] = np.where(G.symbol.isin(top), "top", np.where(G.symbol.isin(bot), "bot", np.where(G.symbol.isin(q.index), "mid", "unranked")))
        rows.append(G)
        out.append(dict(cut=cut, setup=s[:26], **{f"{k}_n": int((G.grp == k).sum()) for k in ("top", "mid", "bot", "unranked")},
                        **{f"{k}_avg": round(float(G.r[G.grp == k].mean()), 3) if (G.grp == k).any() else None for k in ("top", "mid", "bot", "unranked")}))
    A = pd.concat(rows)
    for k in ("top", "bot"):
        d, t = diff_t(A.r, (A.grp == k).to_numpy(), A.date)
        print(cut, "pooled", k, "n", int((A.grp == k).sum()), "avg", round(A.r[A.grp == k].mean(), 3), "vs rest diff", round(d, 3), "t", round(t, 2))
    tb = A[A.grp.isin(["top", "bot"])]
    print(cut, "top-bot", diff_t(tb.r, (tb.grp == "top").to_numpy(), tb.date))
print(pd.DataFrame(out).to_string())
