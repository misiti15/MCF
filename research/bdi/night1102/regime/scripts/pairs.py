"""night1102/regime step 3: complementary PAIRS of live setups (30+ live trades each). For each pair, over the
sessions in which BOTH were live (between each setup's first and last live trade date), combined sum R and avg R per
trade by EOD type (eod3 up/down/quiet). A pair 'hedges' if combined R > 0 in all three types (each with >= 2
sessions). Every pair scored is counted. Educational only - not financial advice."""
import itertools
import sys
from pathlib import Path

import numpy as np
import pandas as pd

SCR = Path(sys.argv[1])
OUT = Path(__file__).resolve().parents[1]
T = pd.read_parquet(SCR / "tagged.parquet")
D = pd.read_parquet(SCR / "days.parquet")
cnt = T.groupby("strategy").size()
S = list(cnt[cnt >= 30].index)
span = T.groupby("strategy").date.agg(["min", "max"])
side = T.groupby("strategy").side.mean()
dayR = T.groupby(["strategy", "date"]).R.agg(["sum", "size"])
alld = sorted(T.date.unique())
rows = []
for a, b in itertools.combinations(S, 2):
    lo, hi = max(span.loc[a, "min"], span.loc[b, "min"]), min(span.loc[a, "max"], span.loc[b, "max"])
    days = [d for d in alld if lo <= d <= hi]
    if len(days) < 8:
        continue
    r = {"a": a, "b": b, "sides": ("L" if side[a] > 0 else "S") + ("L" if side[b] > 0 else "S"), "sessions": len(days)}
    tot = []
    for d in days:
        s = n = 0.0
        for k in (a, b):
            if (k, d) in dayR.index:
                s += dayR.loc[(k, d), "sum"]; n += dayR.loc[(k, d), "size"]
        tot.append((d, D.loc[d, "eod3"], s, n))
    x = pd.DataFrame(tot, columns=["date", "eod3", "R", "n"])
    r["sumR"], r["n"] = x.R.sum(), x.n.sum()
    r["green_days"] = (x.R > 0).mean()
    for L in ("up", "down", "quiet"):
        y = x[x.eod3 == L]
        r[f"{L}_d"], r[f"{L}_R"], r[f"{L}_avg"] = len(y), y.R.sum(), y.R.sum() / max(y.n.sum(), 1)
    rows.append(r)
P = pd.DataFrame(rows)
P["hedge"] = (P.up_R > 0) & (P.down_R > 0) & (P.quiet_R > 0) & (P.up_d >= 2) & (P.down_d >= 2) & (P.quiet_d >= 2)
P["minR"] = P[["up_R", "down_R", "quiet_R"]].min(axis=1)
P.round(3).to_csv(OUT / "pairs_live.csv", index=False)
print("pairs scored", len(P), "hedge", P.hedge.sum(), P[P.hedge].sides.value_counts().to_dict())
pd.set_option("display.width", 300)
print(P.sort_values("minR", ascending=False).head(25).round(2).to_string(index=False))
