"""Summarise diag.py (descriptive; per unit beta, A5 trade set = p05 S3 + cost5). Educational only - not financial advice."""
import glob
import numpy as np, pandas as pd
D = pd.concat([pd.read_parquet(p) for p in sorted(glob.glob("/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/pdl1030b/diag/d_*.parquet"))])
d = D["date"].astype(str); assert (d <= "2026-09-15").all() and not ((d >= "2024-11-01") & (d <= "2025-02-28")).any()
D = D[D.c5 & np.isfinite(D.gross_close)]
print("n", len(D), "stock r_S3", round(D.r_S3.mean(), 4))
for k in ("gross_close", "gross_worse", "cost"):
    print(k, round(D[k].mean(), 4))
print("conservative-fill adj", round((D.gross_worse - D.gross_close).mean(), 4))
r = D.r_S3 + D.gross_close - D.cost  # beta 1, exit-bar close fills (optimistic sensitivity)
g = (r - r.mean()).groupby(D.date).sum(); t = r.mean() / (np.sqrt((g ** 2).sum()) / len(r))
print("pair beta1 at exit-bar closes (sensitivity):", round(r.mean(), 4), "t", round(t, 2), "sd", round(r.std(), 3), "stock sd", round(D.r_S3.std(), 3))
