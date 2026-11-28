"""shorts_autopsy live loader: closed live trades (run 1) from all 10 journals (git show, read-only), LR8 R after costs,
with the submitted signal's spread_bps / bar_time and journal mae_r / mfe_r. Identical signals across accounts counted
once (first account in BRANCHES order). Writes <OUT>/live.parquet. Educational only - not financial advice."""
import sys, sqlite3, subprocess, tempfile
import numpy as np, pandas as pd
from mcf.config import load_config
from mcf.costs import cost_r_lr8
from mcf.research.shadow_calib import BRANCHES
OUT = sys.argv[1]
cfg = load_config(); TP = []
for acct, br in BRANCHES.items():
    raw = subprocess.run(["git", "-C", "/home/user/MCF", "show", f"origin/{br}:journal.db"], capture_output=True).stdout
    if not raw:
        print("no", acct); continue
    with tempfile.NamedTemporaryFile(suffix=".db", dir=OUT) as f:
        f.write(raw); f.flush(); del raw
        con = sqlite3.connect(f.name)
        x = pd.read_sql("SELECT strategy, symbol, side, date, signal_time, entry_time, exit_time, entry, stop, target, exit, "
                        "exit_reason, meta, shares, pnl, pnl_adj, r_multiple, mae_r, mfe_r, broker_order_id FROM trades "
                        "WHERE run_id=1 AND exit_time IS NOT NULL", con)
        s = pd.read_sql("SELECT broker_order_id, info FROM signals WHERE run_id=1 AND status='submitted' AND broker_order_id IS NOT NULL", con)
        sk = pd.read_sql("SELECT strategy, symbol, side, date, entry_time, entry, stop, exit, exit_reason, r_multiple, meta FROM trades WHERE run_id=2 AND meta LIKE 'status=skipped%'", con)
        con.close()
    x["account"] = acct; sk["account"] = acct
    s["spread_bps"] = s["info"].str.extract(r'"spread_bps": ([\d.]+)')[0].astype(float)
    s["bar_time"] = s["info"].str.extract(r'"bar_time": "(\d+)"')[0]
    x = x.merge(s.drop(columns="info").drop_duplicates("broker_order_id"), on="broker_order_id", how="left")
    TP.append(x); sk.to_parquet(f"{OUT}/skips_{acct}.parquet"); print(acct, len(x), len(sk), flush=True)
t = pd.concat(TP, ignore_index=True)
t["date"] = t["date"].astype(str).str[:10]
t["r"] = cost_r_lr8(t, cfg).astype(float)
t = t[t.r.notna()].copy()
t["k"] = t.strategy + "|" + t.symbol + "|" + t.date + "|" + t.entry_time.astype(str).str[:16]
t = t.drop_duplicates("k").drop(columns=["meta"])
t.to_parquet(f"{OUT}/live.parquet"); print(len(t))
