"""FIT-only diagnosis of BEG-07 base losers. Educational only - not financial advice."""
import sys
import numpy as np
import pandas as pd
W = "/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/beg07w"
b = pd.read_parquet(f"{W}/bk_base_fit.parquet")
assert set(b.date.map(lambda d: d[:7])) <= {"2024-10"} | {f"2025-0{m}" for m in range(3, 10)}
print("by exit kind\n", b.groupby("kind").agg(n=("r", "size"), r=("r", "mean"), g=("r_gross", "mean")))
print("stop cost r mean", b.stop_cost_r.mean().round(3), " cost drag", (b.r_gross - b.r).mean().round(3))
w = b.nsmallest(int(len(b) * 0.1), "r")
print("worst 10%:", len(w), "stop share", (w.kind == 1).mean().round(2), "avg r", w.r.mean().round(2))
for col, bins in (("r_sig", [-100, -10, -6, -4, -3, 3, 4, 6, 10, 100]), ("atr_pct", [0, 2, 3, 4, 6, 100]),
                  ("lod_dist_atr", [0, .1, .25, .5, 1, 100]), ("hod_dist_atr", [0, .1, .25, .5, 1, 100]),
                  ("stop_cost_r", [0, .05, .08, .1, .12, .15])):
    g = b.groupby(pd.cut(b[col], bins), observed=True).agg(n=("r", "size"), r=("r", "mean"), g=("r_gross", "mean"),
                                                           stop=("kind", "mean"))
    print(col, "\n", g.round(3))
print("by side x spy\n", b.assign(spy=b.date.map(lambda d: d)).groupby("side").agg(n=("r","size"), r=("r","mean")))
# exit time of stops
s = b[b.kind == 1]
print("stop minutes after entry median", np.median(s.xm - s.em))
