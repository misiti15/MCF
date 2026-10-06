"""Score every LIVE setup once on the Apr-Jun 2026 locked holdout with the production engine (joint portfolio,
real slot limits, production costs). The live setups were approved before this holdout existed (owner rule 2:
a setup must hold on both holdouts). Lead, 2026-10-06. Educational only - not financial advice."""
import json
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, ".")
from mcf.backtest.engine import Backtester
from mcf.config import load_config
from mcf.data.store import BarStore
from mcf.strategies.setups import build_strategies

cfg = load_config()
store = BarStore("data/cache_q2")
data = store.load_many(store.symbols(), start="2026-03-10", end="2026-07-01")
print("symbols", len(data), flush=True)
tr = Backtester(build_strategies(cfg), cfg).run(data)
tr = tr[pd.to_datetime(tr["date"]) >= pd.Timestamp("2026-04-01")]
tr.to_csv("research/rework/holdout/live_q2_trades.csv", index=False)
out = {}
for s, g in tr.groupby("strategy"):
    r = g["r_multiple"].to_numpy()
    d = g.groupby("date")["r_multiple"].agg(["sum", "size"])
    mu = r.mean()
    se = np.sqrt(((d["sum"] - d["size"] * mu) ** 2).sum()) / len(r)
    best = d["sum"].idxmax()
    out[s] = {"n": len(r), "days": len(d), "win_rate": round(float((r > 0).mean()), 3), "exp_r": round(float(mu), 4),
              "t_day_clustered": round(float(mu / se), 2) if se > 0 else None, "pnl": round(float(g["pnl"].sum()), 2),
              "green_days": round(float((d["sum"] > 0).mean()), 3),
              "exp_r_ex_best_day": round(float((d["sum"].sum() - d.loc[best, "sum"]) / max(1, len(r) - d.loc[best, "size"])), 4)}
print(json.dumps(out, indent=1))
json.dump(out, open("research/rework/holdout/live_q2.json", "w"), indent=1)
