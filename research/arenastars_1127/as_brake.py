"""ARENASTARS-1127 Part A add-on: the live records re-cut under BRAKE-BURST (ledger 2026-11-23: at most 30 new entries
per setup in any rolling 10 minutes, per account), entries taken in time order. Educational only - not financial advice."""
import json
import math
import pandas as pd
t = pd.read_csv("research/arenastars_1127/live_trades.csv")
t["ts"] = pd.to_datetime(t.entry_time.str[:19])
keep = []
for (s, d, a), g in t.sort_values("ts").groupby(["strategy", "date", "account"]):
    taken = []
    for i, r in g.iterrows():
        if sum(1 for x in taken if (r.ts - x).total_seconds() < 600) < 30:
            taken.append(r.ts); keep.append(i)
b = t.loc[keep]
out = {}
for s, g in b.groupby("strategy"):
    day = g.groupby("date").r_livel.sum(); dm = g.groupby("date").r_livel.mean()
    best = day.idxmax(); tot = day.sum()
    out[s] = {"n": int(len(g)), "dropped": int((t.strategy == s).sum() - len(g)), "avg": round(g.r_livel.mean(), 4),
              "total": round(tot, 1), "wo_best": round(g[g.date != best].r_livel.mean(), 4),
              "best_share": round(day.max() / tot, 3) if tot > 0 else None,
              "t_day": round(dm.mean() / (dm.std(ddof=1) / math.sqrt(len(dm))), 2)}
print(json.dumps(out, indent=1))
json.dump(out, open("research/arenastars_1127/live_brake.json", "w"), indent=1)
