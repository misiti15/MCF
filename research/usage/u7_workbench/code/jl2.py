"""Live journals (run_id 1, or 3 = shadow) of all accounts with exit fields; R after costs = pnl_adj/(|entry-stop| x shares)."""
import sqlite3, json, numpy as np, pandas as pd
S = "/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/up_u7"
ACC = {"mcf-data": "Primary", "mcf-data-testing": "On Deck", "mcf-data-testing2": "Testing A",
       "mcf-data-explore1": "Testing B", "mcf-data-livelab": "Testing C", "mcf-data-testingd": "Testing D",
       "mcf-data-testinge": "Testing E", "mcf-data-testingf": "Testing F", "mcf-data-gen": "Gen", "mcf-data-graveyard": "Graveyard"}
COLS = "id,symbol,strategy,side,date,signal_time,entry_time,entry,stop,target,exit_time,exit,exit_reason,r_multiple,mae_r,mfe_r,shares,pnl,pnl_adj,meta"
def load(run=1, last="2026-11-17", strategies=None):
    out = []
    for b, a in ACC.items():
        c = sqlite3.connect(f"{S}/j/{b}.db")
        t = pd.read_sql(f"select {COLS} from trades where run_id={run}", c)
        t["acct"] = a; out.append(t)
    t = pd.concat(out, ignore_index=True)
    if strategies is not None: t = t[t.strategy.isin(strategies)]
    t = t[(t.date <= last) & ~t.date.between("2024-11-01", "2025-02-28")].copy()
    risk = (t.entry - t.stop).abs() * t.shares.abs()
    t["risk"] = risk
    t["R"] = np.where(t.pnl_adj.notna() & (risk > 0), t.pnl_adj / risk, t.r_multiple)
    def m(s, k):
        try: return json.loads(s.split(";")[0]).get(k)
        except Exception: return None
    t["stop_cost_r"] = [m(s, "stop_cost_r") if isinstance(s, str) else None for s in t.meta]
    t["spread_bps"] = [m(s, "spread_bps") if isinstance(s, str) else None for s in t.meta]
    t["et"] = pd.to_datetime(t.entry_time, utc=True, format="mixed").dt.tz_convert("America/New_York")
    t["xt"] = pd.to_datetime(t.exit_time, utc=True, format="mixed").dt.tz_convert("America/New_York")
    return t.reset_index(drop=True)
