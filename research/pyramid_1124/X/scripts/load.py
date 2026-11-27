"""Pull closed live trades (run 1) from all 10 account journals with times, MFE/MAE, exit reason, LR8 R and $ cost."""
import os, sys, sqlite3, subprocess, tempfile
import pandas as pd
INBOX = "/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/inbox"
OUT = "/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/pyramid/X/live_all.parquet"
sys.path.insert(0, INBOX); os.chdir(INBOX)
from mcf.config import load_config
from mcf.costs import cost_r_lr8, lot_costs, live_model, parts_from_row
from mcf.research.shadow_calib import BRANCHES
cfg = load_config(); model = live_model(cfg)
parts = []
for acct, br in BRANCHES.items():
    raw = subprocess.run(["git", "show", f"origin/{br}:journal.db"], capture_output=True).stdout
    with tempfile.NamedTemporaryFile(suffix=".db", dir=os.path.dirname(OUT)) as f:
        f.write(raw); f.flush()
        con = sqlite3.connect(f.name)
        x = pd.read_sql("SELECT strategy, symbol, side, date, signal_time, entry_time, exit_time, entry, stop, target, exit, "
                        "exit_reason, mae_r, mfe_r, meta, shares, pnl, pnl_adj, r_multiple FROM trades WHERE run_id=1 AND exit_time IS NOT NULL", con)
        con.close()
    x["account"] = acct; parts.append(x); print(acct, len(x), flush=True)
t = pd.concat(parts, ignore_index=True)
t["date"] = t["date"].astype(str).str[:10]
t["r"] = cost_r_lr8(t, cfg).astype(float)
# $ cost and cost in R (LR8 model on every row)
cr, cd = [], []
for _, row in t.iterrows():
    try:
        risk = abs(float(row["entry"]) - float(row["stop"])) * abs(float(row["shares"]))
        tg = row["target"]; tg = None if tg is None or pd.isna(tg) else float(tg)
        c = lot_costs(int(row["side"]), float(row["entry"]), float(row["shares"]), parts_from_row(row), tg, row["date"], model)["total"]
        cd.append(c); cr.append(c / risk if risk > 0 else float("nan"))
    except Exception:
        cd.append(float("nan")); cr.append(float("nan"))
t["cost_usd"] = cd; t["cost_r"] = cr
t["notional"] = t["entry"].astype(float) * t["shares"].abs().astype(float)
t["gross_r"] = t["pnl"].astype(float) / (abs(t["entry"] - t["stop"]) * t["shares"].abs())
t = t.drop(columns=["meta"])
t.to_parquet(OUT); print(len(t))
