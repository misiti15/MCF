"""NEVERAGAIN live replay scoring. Usage: python score_live.py LIVEDIR BOOK. Educational only - not financial advice."""
import sys
from pathlib import Path
import numpy as np
import pandas as pd

L = Path(sys.argv[1]); BOOK = sys.argv[2]
o = pd.read_csv(L / f"replay_primary_{BOOK}.csv")
D = o.groupby(["date", "cfg"]).R.sum().unstack()
T = pd.read_parquet(L / "lots_all.parquet"); T = T[T.account == "primary"]
if BOOK == "RAW":
    D["ACT"] = T.groupby("date").r.sum().reindex(D.index)
rows = []
for win, idx in (("10-06..", D.index), ("10-29..", D.index[D.index >= "2026-10-29"])):
    b = D.loc[idx, "NOW"]
    for c in D.columns:
        x = D.loc[idx, c]; dr = x - b
        rows.append(dict(window=win, cfg=c, days=len(x), R=round(x.sum(), 1), dR=round(dr.sum(), 1),
                         t=round(dr.mean() / dr.std(ddof=1) * np.sqrt(len(dr)), 2) if dr.std() > 0 else np.nan,
                         worst=round(x.min(), 1), worst_day=x.idxmin(), w5=round(x.nsmallest(5).mean(), 1),
                         red=int((x < 0).sum()), r2g=int(((b < 0) & (x > 0)).sum()), g2r=int(((b > 0) & (x < 0)).sum()),
                         today=round(x.get("2026-11-25", np.nan), 1)))
pd.set_option("display.width", 250)
r = pd.DataFrame(rows); print(r.to_string(index=False))
P = o.groupby(["strategy", "cfg"]).R.sum().unstack()
dP = P.sub(P["NOW"], axis=0).round(1)
dP = dP[(dP.abs() > 0.05).any(axis=1)]
print("\nper-setup dR vs NOW (setups with any change):\n", dP.to_string())
print("\nimprove / worse (>0.5R) by cfg:", {c: (int((dP[c] > 0.5).sum()), int((dP[c] < -0.5).sum())) for c in dP.columns})
print("\ndaily R:\n", D.round(1).to_string())
r.to_csv(L.parent / f"live_results_{BOOK}.csv", index=False); dP.to_csv(L.parent / f"live_per_setup_{BOOK}.csv")
