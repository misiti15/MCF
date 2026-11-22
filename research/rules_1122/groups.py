"""Underlying-market groups for the live symbols: average-linkage clusters of |daily-return correlation| >= 0.80
(1 - |corr| <= 0.20) on 2025-10-01..2026-09-30 daily closes (research/history2y daily.parquet; the locked block is not
in that window). Each member carries a sign vs the group's most liquid member (inverse ETFs = -1), so a long SQQQ and a
short QQQ count as the same bet; leveraged and plain ETFs on one index fall in one group. Symbols without data are their
own group. Usage: python groups.py WORK -> WORK/groups.csv. Educational only - not financial advice."""
import sys
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.cluster.hierarchy import fcluster, linkage
from scipy.spatial.distance import squareform
W = Path(sys.argv[1])
syms = sorted(set(pd.read_parquet(W / "live.parquet", columns=["symbol"]).symbol))
d = pd.read_parquet("/home/user/MCF/research/history2y/data/daily.parquet", columns=["symbol", "date", "close", "dollar_volume"],
                    filters=[("date", ">=", pd.Timestamp("2025-10-01").date()), ("date", "<=", pd.Timestamp("2026-09-30").date())])
d["date"] = d["date"].astype(str)
assert not ((d.date >= "2024-11-01") & (d.date <= "2025-02-28")).any()
d = d[d.symbol.isin(syms)]
P = d.pivot(index="date", columns="symbol", values="close").sort_index()
R = P.pct_change(fill_method=None)
ok = [s for s in R.columns if R[s].notna().sum() >= 120]
C = R[ok].corr(min_periods=120).fillna(0).to_numpy()
dist = np.clip(1 - np.abs(C), 0, 2)
np.fill_diagonal(dist, 0)
Z = linkage(squareform(dist, checks=False), "average")
lab = fcluster(Z, t=0.20, criterion="distance")
dv = d.groupby("symbol").dollar_volume.median()
rows = []
for c in np.unique(lab):
    mem = [ok[i] for i in np.flatnonzero(lab == c)]
    lead = max(mem, key=lambda s: dv.get(s, 0))
    li = ok.index(lead)
    for s in mem:
        rows.append(dict(symbol=s, group=lead, sign=int(np.sign(C[ok.index(s), li]) or 1), size=len(mem)))
for s in syms:
    if s not in ok:
        rows.append(dict(symbol=s, group=s, sign=1, size=1))
g = pd.DataFrame(rows)
g.to_csv(W / "groups.csv", index=False)
big = g[g["size"] > 1].groupby("group").symbol.apply(lambda x: " ".join(sorted(x)))
print(len(g), "symbols;", (g["size"] > 1).sum(), "in", big.size, "multi-member groups")
for k, v in big.items():
    print(k, ":", v[:300])
