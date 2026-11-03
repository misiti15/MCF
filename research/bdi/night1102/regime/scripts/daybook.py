"""night1102/regime: per-session live R of the long and short books (all accounts, paper) next to the session's
point-in-time state, plus SPY first-hour range vs the 20-day median full-day range. Educational only."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

SCR = Path(sys.argv[1])
T = pd.read_parquet(SCR / "tagged.parquet")
D = pd.read_parquet(SCR / "days.parquet")
b = pd.read_parquet(SCR / "idx_1min.parquet")
s = b[b.symbol == "SPY"].copy()
s["tod"] = s.index.hour * 100 + s.index.minute
for t in (950, 1030):
    g = s[s.tod < t].groupby("date")
    D[f"rng@{t}"] = (g.high.max() - g.low.min()) / g.open.first() * 100
    D[f"rngr@{t}"] = D[f"rng@{t}"] / D["med20"]
D.to_parquet(SCR / "days.parquet")
P = T[T.acct == "P"]
x = pd.DataFrame({
    "L_all": T[T.side > 0].groupby("date").R.sum(), "S_all": T[T.side < 0].groupby("date").R.sum(),
    "nL": T[T.side > 0].groupby("date").size(), "nS": T[T.side < 0].groupby("date").size(),
    "P_L": P[P.side > 0].groupby("date").R.sum(), "P_S": P[P.side < 0].groupby("date").R.sum(),
    "P": P.groupby("date").R.sum(), "nP": P.groupby("date").size()})
x = x.join(D[["o2c", "eod3", "eod4", "fo_SPY@1000", "vw_SPY@1000", "fo_SPY@1030", "vw_SPY@1030", "br@1030",
              "rngr@950", "rngr@1030"]])
pd.set_option("display.width", 250)
print(x.round(2).to_string())
