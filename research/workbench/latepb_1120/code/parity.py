import sys, math
from pathlib import Path
import pandas as pd, numpy as np
sys.argv = [sys.argv[0], sys.argv[1]]
exec(open(Path(__file__).parent / "score.py").read().split("N = len(GRID)")[0])
P = trades(PARENT); V = trades((1400, 0.08, -0.069, 20e6))
for nm, t in (("parent", P), ("macd0.08", V)):
    x = t[(t.date >= "2026-10-27")]
    print(nm, "live-window bench trades", len(x), "days", x.date.nunique(), "avg", round(x.r.mean(), 3))
    print(x.groupby("date").agg(n=("r", "size"), r=("r", "mean")).round(3).T.to_string())
    m = t.assign(mo=t.date.str[:7]).groupby("mo").r.agg(["size", "mean"]).round(3)
    print(m.T.to_string())
# paired FIT
d = days[h == "fit"]
a = P[P.half == "fit"].groupby("date").r.sum().reindex(d, fill_value=0); b = V[V.half == "fit"].groupby("date").r.sum().reindex(d, fill_value=0)
df = b - a; print("FIT paired", round(df.mean(), 3), round(df.mean() / (df.std() / math.sqrt(len(df))), 2))
ex = V.merge(P[["symbol", "date"]], on=["symbol", "date"], how="left", indicator=True)
ex = ex[ex._merge == "left_only"]
print("extra trades of macd0.08 (not in parent): FIT", ex[ex.half == "fit"].r.agg(["size", "mean"]).round(3).to_dict(), "CHECK", ex[ex.half == "check"].r.agg(["size", "mean"]).round(3).to_dict())
