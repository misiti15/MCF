"""Paired 2-year exit deltas (from test2y_exits.py output) with day-clustered t, up/down regime split and months helped.
Usage: python exits2y_report.py <scratch>"""
import sys
from pathlib import Path
import numpy as np, pandas as pd
sys.path.insert(0, "/home/user/MCF/research/history2y")
import lib
S = Path(sys.argv[1]); R = pd.read_parquet(S / "exits2y.parquet")
rg = lib.regimes().reset_index()
rg["date"] = pd.to_datetime(rg["date"]).dt.date.astype(str)
R = R.merge(rg[["date", "regime"]], on="date", how="left")
rows = []
for v in ["wide15", "scr60", "ts60", "be03", "part05"]:
    d = R[v] - R.base
    day = d.groupby(R.date).sum(); mo = day.groupby(day.index.str[:7]).sum()
    r = dict(variant=v, n=len(R), base=R.base.mean(), var=R[v].mean(), delta=d.mean(), day_t=day.mean() / (day.std(ddof=1) / np.sqrt(len(day))),
             months_helped=f"{int((mo > 0).sum())}/{len(mo)}")
    for g in ("up", "flat", "down"):
        m = R.regime == g; r[f"delta_{g}"] = d[m].mean()
    rows.append(r)
o = pd.DataFrame(rows); o.to_csv(Path(__file__).parent / "exits_2y.csv", index=False, float_format="%.4f")
print( R.regime.value_counts().to_dict()); print(o.round(4).to_string())
