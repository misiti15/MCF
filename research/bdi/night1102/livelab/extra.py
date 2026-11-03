"""livelab extra: kill rules killed-vs-kept later avg R, session-based kills, same-dates account comparison.
Usage: python extra.py <scratch>. Educational only - not financial advice."""
import sqlite3, sys, json
from pathlib import Path
import pandas as pd, numpy as np
S = Path(sys.argv[1]); OUT = Path(__file__).parent
A = {"primary": "mcf-data", "testing1": "mcf-data-testing", "testing2": "mcf-data-testing2", "graveyard": "mcf-data-graveyard", "gen": "mcf-data-gen"}
T = []
for a, b in A.items():
    t = pd.read_sql("select * from trades where run_id=1", sqlite3.connect(S / f"{b}.db")); t["account"] = a; T.append(t)
T = pd.concat(T); T["risk"] = (T.entry - T.stop).abs() * T.shares; T = T[(T.risk > 0) & T.pnl_adj.notna()].copy()
T["R"] = T.pnl_adj / T.risk; T = T.sort_values(["account", "strategy", "date", "entry_time"])
res = {}
rows = []
for kind, K in (("trades", 30), ("trades", 45), ("sessions", 5), ("sessions", 10)):
    for x in (-0.30, -0.20, -0.10):
        kl, kp = [], []
        for (a, s), g in T.groupby(["account", "strategy"]):
            days = sorted(g.date.unique())
            if kind == "trades":
                if len(g) < K + 15: continue
                e, l = g.iloc[:K], g.iloc[K:]
            else:
                if len(days) < K + 3 or len(g) < 30: continue
                e, l = g[g.date.isin(days[:K])], g[~g.date.isin(days[:K])]
            (kl if e.R.mean() <= x else kp).append((l.R.mean(), len(l), l.R.sum(), l.date.nunique()))
        f = lambda L: dict(setups=len(L), later_avgR_per_setup=round(np.mean([v[0] for v in L]), 3) if L else None,
                           later_pos=sum(v[0] > 0 for v in L), later_R=round(sum(v[2] for v in L), 1),
                           later_avgR_pooled=round(sum(v[2] for v in L) / max(1, sum(v[1] for v in L)), 3))
        rows.append(dict(rule=f"{kind}{K}<= {x}", killed=f(kl), kept=f(kp)))
res["kill_vs_kept"] = rows
# same dates account comparison
d0 = "2026-10-21"
res["same_dates_from_1021"] = T[T.date >= d0].groupby("account").R.agg(["size", "mean"]).round(3).reset_index().to_dict("records")
# first-session-of-setup effect: avg R by setup age (sessions since setup's first live day)
T["age"] = T.groupby(["account", "strategy"]).date.rank(method="dense")
res["by_age"] = T.assign(b=pd.cut(T.age, [0, 5, 10, 15, 30])).groupby("b", observed=True).R.agg(["size", "mean"]).round(3).reset_index().astype(str).to_dict("records")
# setups per account with >=30 trades and >=10 sessions (verdict-ready) and age distribution
g = T.groupby(["account", "strategy"]).agg(n=("R", "size"), s=("date", "nunique"), avg=("R", "mean"))
res["verdict_ready"] = g.assign(ready=(g.n >= 30) & (g.s >= 10)).groupby("account").agg(setups=("n", "size"), ready=("ready", "sum"),
     lt30trades=("n", lambda v: int((v < 30).sum()))).reset_index().to_dict("records")
res["trades_per_session_per_setup_median"] = g.assign(tps=g.n / g.s).groupby("account").tps.median().round(2).to_dict()
json.dump(res, open(OUT / "extra.json", "w"), indent=1, default=float); print(json.dumps(res, indent=1, default=float))
