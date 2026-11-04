"""latch_1103 step (b): live (paper) latch what-if per setup-day, 2026-10-06..2026-11-03, five accounts.
"Off" sequence = run-1 trades + run-2 what-if trades of signals skipped for 'setup daily loss limit'. Each level is
simulated on that sequence (latched; realised R from exits at or before the entry minute). Usage:
python live.py <scratch> (expects <scratch>/j_<acct>.db from origin/mcf-data*:journal.db) -> <scratch>/live_days.parquet.
Educational only - not financial advice."""
import sqlite3, sys
from pathlib import Path
import numpy as np, pandas as pd
from latch import sim_day, LEVELS

S = Path(sys.argv[1])
rows = []
for acct in ("primary", "testing", "testing2", "graveyard", "gen"):
    c = sqlite3.connect(S / f"j_{acct}.db")
    q = ("select strategy setup, date, side, entry_time, signal_time, exit_time, r_multiple r, meta, run_id from trades "
         "where date >= '2026-10-06' and exit_time is not null and r_multiple is not null")
    t = pd.read_sql(q, c)
    t = t[(t.run_id == 1) | t.meta.fillna("").str.contains("why=setup daily loss limit")].copy()
    t["blocked_live"] = t.run_id == 2
    et = pd.to_datetime(t.entry_time.where(t.run_id == 1, t.signal_time).fillna(t.entry_time), utc=True, format="mixed")
    t["ent"] = et.dt.tz_convert("America/New_York").dt.strftime("%H%M").astype(int)
    t["ext"] = pd.to_datetime(t.exit_time, utc=True, format="mixed").dt.tz_convert("America/New_York").dt.strftime("%H%M").astype(int)
    t["account"] = acct
    rows.append(t)
T = pd.concat(rows, ignore_index=True).sort_values(["account", "setup", "date", "ent"])
out = []
for (acct, su, d), g in T.groupby(["account", "setup", "date"], sort=False):
    r, en, ex = g.r.to_numpy(float), g.ent.to_numpy(), g.ext.to_numpy()
    rec = dict(account=acct, setup=su, date=d, side=int(g.side.iloc[0]), n=len(g), r_off=float(r.sum()),
               n_blocked_live=int(g.blocked_live.sum()), r_blocked_live=float(r[g.blocked_live.to_numpy()].sum()))
    for L in LEVELS:
        rl, nb, tl = sim_day(r, en, ex, L)
        rec[f"d_{L}"] = rl - rec["r_off"]; rec[f"lat_{L}"] = nb is not None and tl is not None; rec[f"nb_{L}"] = nb or 0
        rec[f"tl_{L}"] = tl
    out.append(rec)
O = pd.DataFrame(out)
O.to_parquet(S / "live_days.parquet")
for L in LEVELS:
    print(L, O.groupby("account")[[f"d_{L}", f"lat_{L}"]].sum().round(2).to_dict())
