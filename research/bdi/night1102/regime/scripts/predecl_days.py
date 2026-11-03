"""night1102/regime: the three pre-declared switches (PLAN.md) day by day on the LIVE Primary / core7 / all books,
with the Primary rule-change sub-windows split out (ledger: Primary per-setup -2R daily stop from 10-29; position
size ~$5k 10-28, ~$4k 10-28; many promotions/demotions). Educational only - not financial advice."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

SCR = Path(sys.argv[1])
T = pd.read_parquet(SCR / "tagged.parquet")
D = pd.read_parquet(SCR / "days.parquet")
CORE = ["MF2-open-rsimidhi-flowsell-FD", "RW3-gapdn-rsi5pop-flowsell-short-FD", "RW5-heat30-flowsell-rsi5pop-gapdn-short-FD",
        "L3-gap-slope-fromopen-FD", "L3-gap-slope-rsi5hi-FD", "MF4-h40-open-flowsell-FD", "RW1-gapdn-bounce-flowsell-short-FD"]
A = pd.Series(np.where(D["fo_SPY@1000"] >= 0, "up", "down"), index=D.index)
C = pd.Series(np.where(D["vw_SPY@950"] >= 0, "up", "down"), index=D.index)
B = pd.Series(np.where(D["rngr@950"] >= 0.3, "active", "calm"), index=D.index)


def keepA(t):
    s = t.date.map(A)
    return (t.etod < 1000) | ((t.side < 0) & (s == "up")) | ((t.side > 0) & (s == "down"))


def keepC(t):
    s = t.date.map(C)
    return (t.etod < 950) | ((t.side < 0) & (s == "up")) | ((t.side > 0) & (s == "down"))


def keepB(t):
    return (t.etod < 950) | ~((t.side < 0) & (t.date.map(B) == "calm"))


pd.set_option("display.width", 250)
for bname, t in {"primary": T[T.acct == "P"], "core7": T[T.strategy.isin(CORE)], "all": T}.items():
    rows = []
    for d, x in t.groupby("date"):
        rows.append({"date": d, "eod3": D.loc[d, "eod3"], "SPY@10": "up" if A[d] == "up" else "dn", "calm950": B[d],
                     "n": len(x), "R": x.R.sum(), "A_R": x[keepA(x)].R.sum(), "A_n": keepA(x).sum(),
                     "B_R": x[keepB(x)].R.sum(), "C_R": x[keepC(x)].R.sum(), "C_n": keepC(x).sum()})
    X = pd.DataFrame(rows)
    print(f"\n== {bname}")
    print(X.round(2).to_string(index=False))
    for lab, m in (("10-06..10-28", X.date < pd.Timestamp("2026-10-29").date()),
                   ("10-29..11-02", X.date >= pd.Timestamp("2026-10-29").date())):
        y = X[m]
        print(lab, "sessions", len(y), "R", round(y.R.sum(), 1), "A", round(y.A_R.sum(), 1), "B", round(y.B_R.sum(), 1),
              "C", round(y.C_R.sum(), 1))
    print("by eod3:\n", X.groupby("eod3")[["R", "A_R", "B_R", "C_R"]].sum().round(1))
