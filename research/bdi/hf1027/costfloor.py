"""hf1027 task 4 (live side): does a minimum stop width (entry-side cost 1c + 1 bp <= X of R) help the half-R HF setups?
Live paper trades replayed in replay.py (4,438 trades, 13 setups). Journal rc (costs in) and model R both shown.
Usage: python costfloor.py <scratch> -> costfloor_out.txt   Educational only - not financial advice."""
import sys
from pathlib import Path
import numpy as np, pandas as pd
S = Path(sys.argv[1]); HERE = Path(__file__).resolve().parent
X = pd.read_parquet(S / "replay.parquet")
L = [f"{len(X)} half-R HF live trades; entry-side cost share of R (cost_frac) buckets:"]
X["cf"] = pd.cut(X.cost_frac, [0, 0.03, 0.05, 0.08, 0.12, 9])
L.append(X.groupby("cf", observed=True).agg(n=("rc", "size"), setups=("strategy", "nunique"), win=("rc", lambda r: (r > 0).mean()),
         journal=("rc", "mean"), model=("live", "mean"), gross=("live_gross", "mean"), stop_bps=("stop_bps", "median")).round(3).to_string())
def dayt(d):
    return d.mean() / (d.std(ddof=1) / len(d) ** .5)
for th in (0.05, 0.08):
    k = X.cost_frac <= th
    D = X.assign(kept=np.where(k, X.rc, 0.0)).groupby("date").agg(all=("rc", "sum"), kept=("kept", "sum"), n=("rc", "size"))
    dl = (D.kept - D["all"]); L.append(f"cap cost/R <= {th}: keep {k.mean():.2f} of trades; kept {X.rc[k].mean():+.3f}R vs dropped {X.rc[~k].mean():+.3f}R; "
             f"day-clustered t of (kept - all) per day {dayt(dl):+.2f}; setups where dropped < kept: "
             f"{sum(X[(X.strategy==s)&~k].rc.mean() < X[(X.strategy==s)&k].rc.mean() for s in X.strategy.unique() if ((X.strategy==s)&~k).sum()>=10)} of "
             f"{sum(((X.strategy==s)&~k).sum()>=10 for s in X.strategy.unique())} (with >= 10 dropped)")
txt = "\n".join(L) + "\n\nEducational only - not financial advice.\n"
open(HERE / "costfloor_out.txt", "w").write(txt); print(txt)
