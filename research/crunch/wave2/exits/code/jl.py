"""Live journals (run_id 1) of all ten accounts; R after costs = pnl_adj/(|entry-stop| x shares). Locked block excluded."""
import sqlite3, json, os, numpy as np, pandas as pd
S = os.environ.get("W5S", "<scratch>")
ACC = {"mcf-data": "Primary", "mcf-data-testing": "On Deck", "mcf-data-testing2": "Testing A",
       "mcf-data-explore1": "Testing B", "mcf-data-livelab": "Testing C", "mcf-data-testingd": "Testing D",
       "mcf-data-testinge": "Testing E", "mcf-data-testingf": "Testing F", "mcf-data-gen": "Gen", "mcf-data-graveyard": "Graveyard"}
COLS = "id,symbol,strategy,side,date,signal_time,entry_time,entry,stop,target,exit_time,exit,exit_reason,r_multiple,mae_r,mfe_r,shares,pnl,pnl_adj,slip_bps,meta"
def load(last="2026-11-19"):
    out = []
    for b, a in ACC.items():
        c = sqlite3.connect(f"{S}/j/{b}.db")
        t = pd.read_sql(f"select {COLS} from trades where run_id=1", c); t["acct"] = a; out.append(t)
    t = pd.concat(out, ignore_index=True)
    t = t[(t.date <= last) & ~t.date.between("2024-11-01", "2025-02-28") & t.exit.notna()].copy()
    risk = (t.entry - t.stop).abs() * t.shares.abs()
    t["risk"] = risk
    t["R"] = np.where(t.pnl_adj.notna() & (risk > 0), t.pnl_adj / risk, t.r_multiple)
    t = t[np.isfinite(t.R)]
    # identical signal in >1 account counted once (keep first account in ACC order)
    t["ak"] = t.acct.map({a: i for i, a in enumerate(ACC.values())})
    t = t.sort_values("ak").drop_duplicates(["strategy", "symbol", "date", "side", "signal_time"])
    return t.reset_index(drop=True)
