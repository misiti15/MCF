"""hf1027: per-setup daily loss stop replayed on live paper trades (no new entries of a setup once its REALIZED R
that day, from trades already exited, is <= -X). X in {2, 3, 5} = 3 configurations. Applied to every HF setup
(hf_setups.csv) in its live account; costs in (rc). Live only: the two-year scan has no exit times per trade.
Usage: python daystop.py <scratch> -> daystop_out.txt   Educational only - not financial advice."""
import sys
from pathlib import Path
import numpy as np, pandas as pd
S = Path(sys.argv[1]); HERE = Path(__file__).resolve().parent
H = pd.read_csv(HERE / "hf_setups.csv")
T = pd.read_parquet(S / "all_trades.parquet"); T = T[(T.date >= "2026-10-09") & T.strategy.isin(H.setup)]
def keep(g, X):
    g = g.sort_values("nt"); k = []
    for r in g.itertuples():
        done = g[(g.et <= r.nt)].rc.sum()
        k.append(done > -X)
    return pd.Series(k, index=g.index)
L = []; rows = []
for X in (2, 3, 5):
    T[f"k{X}"] = T.groupby(["acct", "strategy", "date"], group_keys=False).apply(lambda g: keep(g, X))
for s, g in list(T.groupby("strategy")) + [("ALL HF", T)]:
    row = dict(setup=s, n=len(g), base=round(g.rc.mean(), 3), base_sum=round(g.rc.sum(), 1))
    for X in (2, 3, 5):
        k = g[f"k{X}"]; row[f"stop{X}_n"] = int(k.sum()); row[f"stop{X}_sum"] = round(g.rc[k].sum(), 1); row[f"stop{X}_avg"] = round(g.rc[k].mean(), 3)
    rows.append(row)
R = pd.DataFrame(rows); pd.set_option("display.width", 300); pd.set_option("display.max_columns", 30)
L.append(R.to_string(index=False))
for X in (2, 3, 5):
    D = T.assign(kr=np.where(T[f"k{X}"], T.rc, 0)).groupby(["date"]).agg(a=("rc", "sum"), b=("kr", "sum"))
    dl = D.b - D.a; L.append(f"X={X}: total R change {dl.sum():+.1f} over {len(D)} sessions, day-clustered t {dl.mean()/(dl.std(ddof=1)/len(D)**.5):+.2f}, "
                             f"sessions improved {(dl > 0).sum()}, worsened {(dl < 0).sum()}")
txt = "\n".join(L) + "\n\nEducational only - not financial advice.\n"
open(HERE / "daystop_out.txt", "w").write(txt); print(txt)
