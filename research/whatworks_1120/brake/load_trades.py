"""OUT-BRAKE loader: closed live trades (run 1) of every account journal with entry/exit timestamps, R after costs on
the LR8 basis (mcf.costs.cost_r_lr8, same as footrace.live_trades). NOT de-duplicated across accounts (a brake acts per
account on its own trades). Read-only: git show of origin/mcf-data* journals. Educational only - not financial advice."""
import os, sqlite3, subprocess, sys, tempfile
REPO = sys.argv[1]; OUT = sys.argv[2]
sys.path.insert(0, REPO); os.chdir(REPO)
import pandas as pd
from mcf.config import load_config
from mcf.costs import cost_r_lr8
from mcf.research.shadow_calib import BRANCHES
cfg, parts = load_config(), []
for acct, br in BRANCHES.items():
    raw = subprocess.run(["git", "show", f"origin/{br}:journal.db"], capture_output=True).stdout
    if not raw:
        print("skip", acct); continue
    with tempfile.NamedTemporaryFile(suffix=".db") as f:
        f.write(raw); f.flush()
        con = sqlite3.connect(f.name)
        x = pd.read_sql("SELECT * FROM trades WHERE run_id=1 AND exit_time IS NOT NULL", con)
        con.close()
    x["account"] = acct
    x["date"] = x["date"].astype(str).str[:10]
    x["r"] = cost_r_lr8(x, cfg).astype(float)
    parts.append(x.drop(columns=["meta"], errors="ignore"))
    print(acct, len(x))
t = pd.concat(parts, ignore_index=True)
t = t[t["r"].notna() & (t["date"] <= "2026-11-19")]
t.to_parquet(OUT)
print(len(t))
