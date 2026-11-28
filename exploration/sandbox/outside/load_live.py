"""Load all 10 live journals (run 1, closed trades, from 10-23) with LR8 net R and entry/exit times, per account.
Writes live_acct.parquet to the scratch dir (not committed). Read-only. Educational only - not financial advice.
Usage: PYTHONPATH=<worktree> python load_live.py <scratch_dir>"""
import sqlite3, subprocess, tempfile, sys
import pandas as pd
from mcf.config import load_config
from mcf.costs import cost_r_lr8
from mcf.research.shadow_calib import BRANCHES

SCR = sys.argv[1]
cfg, parts = load_config(), []
for acct, br in BRANCHES.items():
    raw = subprocess.run(["git", "-C", "/home/user/MCF", "show", f"origin/{br}:journal.db"], capture_output=True).stdout
    if not raw:
        print("missing", acct); continue
    with tempfile.NamedTemporaryFile(suffix=".db", dir=SCR) as f:
        f.write(raw); f.flush()
        con = sqlite3.connect(f.name)
        x = pd.read_sql("SELECT strategy, symbol, side, date, entry_time, exit_time, entry, stop, target, exit, exit_reason, meta, "
                        "shares, pnl, pnl_adj, r_multiple FROM trades WHERE run_id=1 AND exit_time IS NOT NULL", con)
        con.close()
    x["account"] = acct; parts.append(x)
t = pd.concat(parts, ignore_index=True)
t["date"] = t["date"].astype(str).str[:10]
t = t[t.date >= "2026-10-23"].copy()
t["r"] = cost_r_lr8(t, cfg).astype(float)
t = t[t["r"].notna()].copy()
t["et"] = pd.to_datetime(t.entry_time, errors="coerce", utc=True).dt.tz_convert("America/New_York")
t["xt"] = pd.to_datetime(t.exit_time, errors="coerce", utc=True).dt.tz_convert("America/New_York")
t = t[t.et.notna() & t.xt.notna()]
t["k"] = t.strategy + "|" + t.symbol + "|" + t.date + "|" + t.entry_time.astype(str).str[:16]
t[["account", "strategy", "symbol", "side", "date", "et", "xt", "exit_reason", "r", "k"]].to_parquet(f"{SCR}/live_acct.parquet")
print(len(t), t.date.min(), t.date.max()); print(t.groupby("account").agg(n=("r", "size"), days=("date", "nunique"), R=("r", "sum")).round(1))
