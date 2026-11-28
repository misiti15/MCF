"""Load all 10 live journals (run 1, closed trades) with LR8 net R, gross R, hold minutes, notional.
Identical signals across accounts counted once (first account, same key as footrace.live_trades).
Writes a parquet to the scratch dir (not committed). Read-only. Educational only - not financial advice."""
import sqlite3, subprocess, tempfile, sys, os
import numpy as np, pandas as pd
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
t["r"] = cost_r_lr8(t, cfg).astype(float)
t = t[t["r"].notna()].copy()
risk = (t.entry.astype(float) - t.stop.astype(float)).abs() * t.shares.astype(float).abs()
t["gross_r"] = np.where(risk > 0, t.pnl.astype(float) / risk, np.nan)
t["notional"] = t.entry.astype(float) * t.shares.astype(float).abs()
et, xt = pd.to_datetime(t.entry_time, errors="coerce", utc=True), pd.to_datetime(t.exit_time, errors="coerce", utc=True)
t["hold_min"] = (xt - et).dt.total_seconds() / 60
t["k"] = t.strategy + "|" + t.symbol + "|" + t.date + "|" + t.entry_time.astype(str).str[:16]
t = t.drop_duplicates("k")
t[["account", "strategy", "symbol", "side", "date", "entry_time", "exit_reason", "r", "gross_r", "notional", "hold_min", "shares", "entry"]].to_parquet(f"{SCR}/live.parquet")
print(len(t), t.date.min(), t.date.max()); print(t.groupby("account").size())
print(t[["r", "gross_r", "notional", "hold_min"]].describe().round(3))
