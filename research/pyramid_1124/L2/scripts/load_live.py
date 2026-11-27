"""Load all live run-1 closed trades from the 10 account journals with LR8 R. Educational only - not financial advice."""
import sqlite3, subprocess, tempfile, os, sys
import pandas as pd
INBOX = "/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/inbox"
sys.path.insert(0, INBOX)
from mcf.config import load_config
from mcf.costs import cost_r_lr8
from mcf.research.shadow_calib import BRANCHES
cfg, parts = load_config(), []
for acct, br in BRANCHES.items():
    raw = subprocess.run(["git", "-C", INBOX, "show", f"origin/{br}:journal.db"], capture_output=True).stdout
    if not raw: print("no", acct); continue
    with tempfile.NamedTemporaryFile(suffix=".db", dir=os.path.dirname(__file__) or ".") as f:
        f.write(raw); f.flush(); del raw
        con = sqlite3.connect(f.name)
        x = pd.read_sql("SELECT strategy, symbol, side, date, entry_time, exit_time, entry, stop, target, exit, exit_reason, meta, shares, pnl, pnl_adj, r_multiple FROM trades WHERE run_id=1 AND exit_time IS NOT NULL", con)
        con.close()
    x["account"] = acct; parts.append(x); print(acct, len(x))
t = pd.concat(parts, ignore_index=True)
t["date"] = t["date"].astype(str).str[:10]
t["r"] = cost_r_lr8(t, cfg).astype(float)
t = t[t["r"].notna()]
t["k"] = t["strategy"] + "|" + t["symbol"] + "|" + t["date"] + "|" + t["entry_time"].astype(str).str[:16]
t["dup"] = t.duplicated("k")
t.drop(columns=["meta"]).to_csv("live_all.csv.gz", index=False)
print(len(t), t.dup.sum())
