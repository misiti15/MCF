"""What-if (run 2: signals not taken) outcomes by skip reason vs live (run 1), both GROSS r_multiple (what-if rows carry
no cost basis), since 11-12. Shows how many free counterfactual reps the journals already hold. Read-only.
Usage: python whatif.py <dbdir>. Educational only - not financial advice."""
import sqlite3, sys, re
from pathlib import Path
import numpy as np, pandas as pd
from mcf.research.shadow_calib import BRANCHES

def dayt(x):
    x = np.asarray(x, float)
    return 0.0 if len(x) < 3 or x.std(ddof=1) == 0 else x.mean() / (x.std(ddof=1) / np.sqrt(len(x)))

parts = []
for acct, br in BRANCHES.items():
    con = sqlite3.connect(Path(sys.argv[1]) / f"{br}.db")
    x = pd.read_sql("SELECT run_id, strategy, symbol, side, date, r_multiple, meta FROM trades WHERE run_id IN (1,2) "
                    "AND exit_time IS NOT NULL AND date >= '2026-11-12'", con)
    con.close(); x["account"] = acct; parts.append(x)
t = pd.concat(parts); t["date"] = t.date.astype(str).str[:10]
t["why"] = np.where(t.run_id == 1, "LIVE (taken)", t.meta.fillna("").str.extract(r"why=([^;:(]+)")[0].fillna("?").str.strip())
t["why"] = t.why.str.replace(r"\d+(\.\d+)?", "#", regex=True).str[:40]
rows = []
for w, g in t.groupby("why"):
    if len(g) < 100: continue
    dm = g.groupby("date").r_multiple.mean()
    rows.append(dict(reason=w, n=len(g), setups=g.strategy.nunique(), gross_avg=round(g.r_multiple.mean(), 3),
                     day_t=round(dayt(dm), 2), short_share=round((g.side < 0).mean(), 2)))
r = pd.DataFrame(rows).sort_values("n", ascending=False)
print(r.to_string(index=False))
live = (t.run_id == 1).sum(); wi = (t.run_id == 2).sum()
print(f"live rows {live}, what-if rows {wi}, ratio {wi/live:.2f}")
