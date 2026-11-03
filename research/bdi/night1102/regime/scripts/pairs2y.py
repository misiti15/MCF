"""night1102/regime: the live pairs that 'hedged' (combined R > 0 in up/down/quiet) re-checked on the two-year
signals (scan2y.py, costs in), plus the core gap-down/flow-sell short family as a book. Sum R per session by eod3,
TRAIN / VALID. Educational only - not financial advice."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

SCR = Path(sys.argv[1])
OUT = Path(__file__).resolve().parents[1]
D = pd.read_parquet(SCR / "days2y.parquet")
S = pd.concat([pd.read_parquet(p) for p in sorted((SCR / "sig2y").glob("*.parquet"))], ignore_index=True)
S["date"] = pd.to_datetime(S["date"]).dt.date
S = S[S.date.isin(set(D.index))].dropna(subset=["R"])
S["split"] = np.where(S.date <= pd.Timestamp("2025-12-31").date(), "train", "valid")
P = pd.read_csv(OUT / "pairs_live.csv")
P = P[P.hedge]
CORE = ["MF2-open-rsimidhi-flowsell-FD", "RW3-gapdn-rsi5pop-flowsell-short-FD", "RW5-heat30-flowsell-rsi5pop-gapdn-short-FD",
        "L3-gap-slope-fromopen-FD", "L3-gap-slope-rsi5hi-FD", "MF4-h40-open-flowsell-FD", "RW1-gapdn-bounce-flowsell-short-FD"]
books = {f"{r.a} + {r.b}": [r.a, r.b] for r in P.itertuples()}
books["core7 (gap-down / flow-sell shorts)"] = CORE
rows = []
have = set(S.setup)
for name, mem in books.items():
    if not set(mem) <= have:
        rows.append({"book": name, "note": "not covered on 2y: " + ",".join(sorted(set(mem) - have))})
        continue
    x = S[S.setup.isin(mem)]
    r = {"book": name}
    for sp in ("train", "valid"):
        y = x[x.split == sp]
        r[f"{sp}_n"], r[f"{sp}_avg"] = len(y), y.R.mean()
        for L in ("up", "down", "quiet"):
            z = y[y.date.map(D.eod3) == L]
            r[f"{sp}_{L}_avg"] = z.R.mean()
        r[f"{sp}_all3_pos"] = all(r[f"{sp}_{L}_avg"] > 0 for L in ("up", "down", "quiet"))
    rows.append(r)
R = pd.DataFrame(rows)
R.round(4).to_csv(OUT / "pairs_2y.csv", index=False)
pd.set_option("display.width", 300)
print(R.round(3).to_string(index=False))
