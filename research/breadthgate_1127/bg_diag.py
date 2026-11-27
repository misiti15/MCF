"""BREADTHGATE-1127 diagnostic (information only, NOT a configuration, no pass claim): per setup x split, LIVE-L avg R by
BRvw band at entry (< 0.4 / 0.4-0.6 / > 0.6, the VW-S cut points) and the day-clustered t of (weak - strong) band means.
Usage: python bg_diag.py W -> diag.csv. Locked block asserted absent. Educational only - not financial advice."""
import sys
from pathlib import Path
import numpy as np
import pandas as pd
W = Path(sys.argv[1]); H = Path(__file__).resolve().parent
x = pd.read_parquet(W / "lots.parquet")
d = x.date.astype(str); assert not ((d >= "2024-11-01") & (d <= "2025-02-28")).any()
x["band"] = pd.cut(x.breadth, [-1, 0.4, 0.6, 2], labels=["weak", "mid", "strong"])
rows = []
for (s, sp), g in x[x.per.isin(["CHECK", "T2"])].groupby(["setup", "per"]):
    m = g.groupby("band", observed=False).r_live.agg(["mean", "size"])
    dw = g[g.band == "weak"].groupby("date").r_live.mean(); ds = g[g.band == "strong"].groupby("date").r_live.mean()
    se = np.sqrt(dw.var(ddof=1) / max(len(dw), 1) + ds.var(ddof=1) / max(len(ds), 1)) if len(dw) > 1 and len(ds) > 1 else np.nan
    rows.append(dict(setup=s, per=sp, side=int(g.side.iloc[0]), **{f"{b}_avg": m.loc[b, "mean"] for b in m.index},
                     **{f"{b}_n": int(m.loc[b, "size"]) for b in m.index},
                     weak_minus_strong_t=(dw.mean() - ds.mean()) / se if se == se and se > 0 else np.nan))
o = pd.DataFrame(rows); o.to_csv(H / "diag.csv", index=False, float_format="%.4f")
pd.set_option("display.width", 250); print(o.assign(setup=o.setup.str[:28]).round(3).to_string(index=False))
