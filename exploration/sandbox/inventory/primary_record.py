"""Primary live record since Day 1 (10-23): per setup and per day, R after costs (LR8), run 1.
Usage: python primary_record.py <journal.db>   (copy via git show origin/mcf-data:journal.db)
Educational only - not financial advice."""
import sqlite3, sys
import numpy as np, pandas as pd
from mcf.config import load_config
from mcf.costs import cost_r_lr8

con = sqlite3.connect(sys.argv[1])
t = pd.read_sql("SELECT strategy, symbol, side, date, entry_time, entry, stop, target, exit, exit_reason, meta, shares, pnl, "
                "pnl_adj, r_multiple FROM trades WHERE run_id=1 AND exit_time IS NOT NULL", con)
t["date"] = t["date"].astype(str).str[:10]
t = t[t["date"] >= "2026-10-23"].copy()
t["r"] = cost_r_lr8(t, load_config()).astype(float)
t = t[t["r"].notna()]
day = t.groupby("date")["r"].sum()
def dt(s):
    return s.mean() / (s.std(ddof=1) / np.sqrt(len(s))) if len(s) > 2 and s.std() > 0 else float("nan")
print(f"sessions {len(day)}  trades {len(t)}  total {day.sum():+.1f}R  green {int((day>0).sum())}/{len(day)}  "
      f"mean/day {day.mean():+.2f}  day t {dt(day):+.2f}  w/o best day {day.sum()-day.max():+.1f}R  pnl_adj ${t.pnl_adj.sum():,.0f}")
print("\nBy side:"); print(t.groupby("side")["r"].agg(["count","sum","mean"]).round(3))
rows=[]
for s,g in t.groupby("strategy"):
    d=g.groupby("date")["r"].sum(); b=d.idxmax()
    rows.append((s,len(d),len(g),g.r.sum(),g.r.mean(),(g.r.sum()-d.max())/max(len(g[g.date!=b]),1),d.max()/g.r.sum() if g.r.sum()>0 else float('nan'),dt(d)))
r=pd.DataFrame(rows,columns=["setup","sess","tr","totR","avgR","avgR_wo_best","best_share","day_t"]).sort_values("tr",ascending=False)
print("\nBy setup:"); print(r.round(3).to_string(index=False))
w = day.groupby(pd.to_datetime(day.index).to_period("W-FRI")).agg(["count", "sum", lambda s: int((s<=0).sum())])
w.columns=["sess","R","red"]; print("\nBy week:"); print(w.round(1).to_string())
print("\nBy day:"); print(day.round(2).to_string())
