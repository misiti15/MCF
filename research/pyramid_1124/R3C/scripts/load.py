"""R3C: closed live trades (run 1) + their submitted signal (decision-bar close ref_price, bar_time, spread_bps) from the
10 account journals; LR8 cost per trade. Read-only (git show). Educational only - not financial advice."""
import os, sys, sqlite3, subprocess, tempfile, json
import numpy as np, pandas as pd
INBOX = "/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/inbox"
OUT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, INBOX); os.chdir(INBOX)
from mcf.config import load_config
from mcf.costs import cost_r_lr8, lot_costs, live_model, parts_from_row
from mcf.research.shadow_calib import BRANCHES
cfg = load_config(); model = live_model(cfg)
TP, SP = [], []
for acct, br in BRANCHES.items():
    raw = subprocess.run(["git", "show", f"origin/{br}:journal.db"], capture_output=True).stdout
    if not raw: print("no", acct); continue
    with tempfile.NamedTemporaryFile(suffix=".db", dir=OUT) as f:
        f.write(raw); f.flush(); del raw
        con = sqlite3.connect(f.name)
        x = pd.read_sql("SELECT strategy, symbol, side, date, signal_time, entry_time, exit_time, entry, stop, target, exit, "
                        "exit_reason, meta, shares, pnl, pnl_adj, r_multiple, broker_order_id, slip_bps FROM trades "
                        "WHERE run_id=1 AND exit_time IS NOT NULL", con)
        s = pd.read_sql("SELECT day, symbol, strategy, side, ref_price, stop AS sstop, broker_order_id, info FROM signals "
                        "WHERE run_id=1 AND status='submitted' AND broker_order_id IS NOT NULL", con)
        con.close()
    x["account"] = acct; s["account"] = acct
    TP.append(x); SP.append(s); print(acct, len(x), len(s), flush=True)
t = pd.concat(TP, ignore_index=True); s = pd.concat(SP, ignore_index=True)
t["date"] = t["date"].astype(str).str[:10]
t["r"] = cost_r_lr8(t, cfg).astype(float)
cd = []
for _, row in t.iterrows():
    try:
        tg = row["target"]; tg = None if tg is None or pd.isna(tg) else float(tg)
        parts = parts_from_row(row)
        c = lot_costs(int(row["side"]), float(row["entry"]), float(row["shares"]), parts, tg, row["date"], model)
        cd.append((c["total"], c["entry"], c["stop"] + c["target"] + c["market"], len(parts)))
    except Exception:
        cd.append((np.nan,) * 4)
t[["lr8_usd", "lr8_entry_usd", "lr8_exit_usd", "nparts"]] = pd.DataFrame(cd, index=t.index)
t["multi_part"] = t.meta.astype(str).str.contains("exit_parts=")
t = t.drop(columns=["meta"])
s["bar_time"] = s["info"].str.extract(r'"bar_time": "(\d+)"')[0]
s["spread_bps"] = s["info"].str.extract(r'"spread_bps": ([\d.]+)')[0].astype(float)
s = s.drop(columns=["info"]).drop_duplicates(["account", "broker_order_id"])
t = t.merge(s[["account", "broker_order_id", "ref_price", "sstop", "bar_time", "spread_bps"]], on=["account", "broker_order_id"], how="left")
t["k"] = t.strategy + "|" + t.symbol + "|" + t.date + "|" + t.entry_time.astype(str).str[:16] + "|" + t.account
t = t.drop_duplicates("k")
t.to_parquet(OUT + "/live.parquet"); print(len(t), t.ref_price.notna().mean(), t.spread_bps.notna().mean())
