"""Live trades (run 1, LR8 R, identical signals once) with entry time + side; journals copied to scratch then deleted."""
import sqlite3, subprocess, sys, os
from pathlib import Path
import pandas as pd
WT = Path(sys.argv[1]); OUT = Path(sys.argv[2]); J = OUT.parent / "j"
sys.path.insert(0, str(WT))
from mcf.config import load_config
from mcf.costs import cost_r_lr8
from mcf.research.shadow_calib import BRANCHES
cfg, parts = load_config(), []
for acct, br in BRANCHES.items():
    p = J / f"{acct}.db"
    raw = subprocess.run(["git", "-C", "/home/user/MCF", "show", f"origin/{br}:journal.db"], capture_output=True).stdout
    if not raw: continue
    p.write_bytes(raw)
    con = sqlite3.connect(p)
    x = pd.read_sql("SELECT strategy, symbol, side, date, entry_time, entry, stop, target, exit, exit_reason, meta, shares, pnl, pnl_adj, r_multiple FROM trades WHERE run_id=1 AND exit_time IS NOT NULL", con)
    con.close(); p.unlink()
    x["account"] = acct; parts.append(x)
t = pd.concat(parts, ignore_index=True)
t["date"] = t["date"].astype(str).str[:10]
t["r"] = cost_r_lr8(t, cfg).astype(float)
t = t[t["r"].notna()]
t["k"] = t["strategy"] + "|" + t["symbol"] + "|" + t["date"] + "|" + t["entry_time"].astype(str).str[:16]
t = t.drop_duplicates("k")
t[["account","strategy","symbol","side","date","entry_time","entry","stop","r"]].to_parquet(OUT)
print(len(t), t.date.min(), t.date.max(), t.side.unique()[:5])
