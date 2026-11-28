"""regime_filters step 1: run-1 closed lots from all 10 journals (git show, read-only), ALL dates in each journal,
LR8 net R; ET entry/exit times; plus SPY 1-minute bars (Alpaca GET) from 2026-08-01 for point-in-time regime features.
Usage: PYTHONPATH=<worktree> python extract.py <scratch>  -> lots.parquet, spy.parquet
Educational only - not financial advice."""
import sqlite3, subprocess, sys, os
from datetime import datetime
import numpy as np, pandas as pd
from mcf.config import load_config
from mcf.costs import cost_r_lr8
from mcf.research.shadow_calib import BRANCHES, family_of
S = sys.argv[1]; cfg = load_config(); parts = []
for acct, br in BRANCHES.items():
    subprocess.run(["git", "-C", "/home/user/MCF", "fetch", "-q", "origin", br])
    raw = subprocess.run(["git", "-C", "/home/user/MCF", "show", f"origin/{br}:journal.db"], capture_output=True).stdout
    fn = f"{S}/j_{acct}.db"; open(fn, "wb").write(raw)
    con = sqlite3.connect(fn)
    x = pd.read_sql("SELECT id, strategy, symbol, side, date, entry_time, exit_time, entry, stop, target, exit, exit_reason, "
                    "shares, pnl, pnl_adj FROM trades WHERE run_id=1 AND exit_time IS NOT NULL", con)
    con.close(); os.remove(fn)
    x["date"] = x["date"].astype(str).str[:10]
    x["r"] = cost_r_lr8(x, cfg).astype(float)
    x["account"] = acct; parts.append(x); print(acct, len(x), x.date.min(), x.date.max(), flush=True)
t = pd.concat(parts, ignore_index=True); t = t[t.r.notna()].copy()
et = pd.to_datetime(t.entry_time, utc=True, format="mixed").dt.tz_convert("America/New_York")
xt = pd.to_datetime(t.exit_time, utc=True, format="mixed").dt.tz_convert("America/New_York")
t["emin"] = et.dt.hour * 60 + et.dt.minute; t["xmin"] = xt.dt.hour * 60 + xt.dt.minute
t["xdate"] = xt.dt.strftime("%Y-%m-%d")
t["family"] = t.strategy.map(family_of); t["sidel"] = np.where(t.side > 0, "long", "short")
t["k"] = t.strategy + "|" + t.symbol + "|" + t.date + "|" + et.dt.strftime("%H:%M")
t[["account", "strategy", "family", "symbol", "sidel", "date", "emin", "xmin", "xdate", "exit_reason", "r", "k"]].to_parquet(f"{S}/lots.parquet")
print("lots", len(t))
from mcf.data.alpaca_data import fetch_bars
b = fetch_bars(["SPY"], datetime(2026, 8, 1), datetime(2026, 11, 28), feed="iex")["SPY"]
b.to_parquet(f"{S}/spy.parquet"); print("spy bars", len(b), b.index.min(), b.index.max())
