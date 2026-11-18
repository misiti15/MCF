"""Live journals (run_id 1) of all accounts; R after costs = pnl_adj/(|entry-stop| x shares)."""
import sqlite3, os, numpy as np, pandas as pd
S = "/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/up_u4"
ACC = {"mcf-data": "Primary", "mcf-data-testing": "On Deck", "mcf-data-testing2": "Testing A",
       "mcf-data-explore1": "Testing B", "mcf-data-livelab": "Testing C", "mcf-data-testingd": "Testing D",
       "mcf-data-testinge": "Testing E", "mcf-data-testingf": "Testing F", "mcf-data-gen": "Gen", "mcf-data-graveyard": "Graveyard"}
def load(last="2026-11-17"):
    out = []
    for b, a in ACC.items():
        c = sqlite3.connect(f"{S}/j/{b}.db")
        t = pd.read_sql("select symbol,strategy,side,date,entry_time,exit_time,entry,stop,shares,pnl,pnl_adj,r_multiple,exit_reason from trades where run_id=1", c)
        t["acct"] = a; out.append(t)
    t = pd.concat(out, ignore_index=True)
    t = t[(t.date <= last) & ~t.date.between("2024-11-01", "2025-02-28")]
    risk = (t.entry - t.stop).abs() * t.shares.abs()
    t["R"] = np.where(t.pnl_adj.notna() & (risk > 0), t.pnl_adj / risk, t.r_multiple)
    return t.reset_index(drop=True)
