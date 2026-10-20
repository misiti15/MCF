"""Parity: 1-minute simulator t1s1/t05s1 (next-minute-open entry) vs lab outcomes (bar-close entry), same rows."""
import json
import numpy as np, pandas as pd
from common import SCR, HERE
S = pd.read_parquet(SCR / "sim.parquet").dropna(subset=["s_t1s1"])
S["date"] = pd.to_datetime(S["date"]).dt.date
T = pd.read_parquet(SCR / "b_trades.parquet", columns=["symbol", "date", "tod", "r_t1s1", "r_t05s1"]).drop_duplicates(["symbol", "date", "tod"])
T["date"] = pd.to_datetime(T["date"]).dt.date
M = S.merge(T, on=["symbol", "date", "tod"])
out = {"rows": len(M)}
for g in ("t1s1", "t05s1"):
    a, b = M["s_" + g].to_numpy(float), M["r_" + g].to_numpy(float)
    ok = np.isfinite(a) & np.isfinite(b)
    out[g] = dict(sim_mean=round(float(a[ok].mean()), 4), lab_mean=round(float(b[ok].mean()), 4),
                  corr=round(float(np.corrcoef(a[ok], b[ok])[0, 1]), 3), same_sign=round(float((np.sign(a[ok]) == np.sign(b[ok])).mean()), 3))
json.dump(out, open(HERE / "parity.json", "w"), indent=1); print(out)
