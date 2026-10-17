"""Summarise the arena single-indicator screen: top cells per (side, window), per-family counts, null check.
    python research/swarm1017/arena/summarize.py > research/swarm1017/arena/summary.txt
Educational only - not financial advice."""
import math
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
res = pd.read_parquet(HERE / "single_screen.parquet")
N = len(res)
bar = max(1.5, math.sqrt(2 * math.log(N)))
pd.set_option("display.width", 250)
pd.set_option("display.max_columns", 40)
print(f"cells (configurations) scored: {N}; try-count bar max(1.5, sqrt(2 ln N)) = {bar:.3f}")
print(f"indicators: {res['indicator'].nunique()}, windows: {sorted(res['window'].unique())}")
big = res[res["n"] >= 200]
print(f"cells with n >= 200: {len(big)}")
for k in ("t", "t_excess"):
    v = big[k].dropna()
    print(f"  {k}: share > 2: {(v > 2).mean():.4f} (null ~0.023), share > bar: {(v > bar).mean():.4f}, max {v.max():.2f}")
print(f"  exp_r > 0: {(big['exp_r'] > 0).mean():.4f}; excess > 0: {(big['excess'] > 0).mean():.4f}")
q = big[(big["exp_r"] > 0) & (big["excess"] > 0) & (big["exp_up"] > 0) & (big["exp_down"] > 0)
        & (big["exp_h1"] > 0) & (big["exp_h2"] > 0)]
print(f"cells passing the screen filter (n>=200, exp>0, excess>0, up>0, down>0, both train halves>0): {len(q)}")
print(f"  of which train t >= bar {bar:.2f}: {(q['t'] >= bar).sum()}; t_excess >= bar: {(q['t_excess'] >= bar).sum()}")
cols = ["indicator", "live", "bin", "op", "lo", "hi", "geom", "n", "days", "exp_r", "t", "excess", "t_excess", "exp_up",
        "exp_down", "exp_h1", "exp_h2"]
for (side, win), g in q.groupby(["side", "window"]):
    print(f"\n=== {side} {win}: {len(g)} cells pass the filter; top 10 by t_excess")
    print(g.sort_values("t_excess", ascending=False)[cols].head(10).to_string(index=False, float_format=lambda x: f"{x:.3f}"))
print("\n=== family x side: cells passing the filter / cells with n>=200")
a = q.groupby(["family", "side"]).size().unstack(fill_value=0)
b = big.groupby(["family", "side"]).size().unstack(fill_value=0)
print((a.astype(str) + " / " + b.astype(str)).to_string())
print("\n=== baseline: mean control (random same-minute) R by side, geom, window (train sample)")
print(res.groupby(["side", "geom", "window"]).apply(lambda g: np.average(g["exp_r"] - g["excess"], weights=g["n"])).unstack().round(4).to_string())
