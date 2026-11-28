"""All 10 accounts, run 1, since 10-23: long vs short R after costs (LR8), identical signals counted once.
Reads journals via git show into a temp file (deleted). Educational only - not financial advice."""
import sqlite3, subprocess, tempfile
import numpy as np, pandas as pd
from mcf.config import load_config
from mcf.costs import cost_r_lr8
from mcf.research.shadow_calib import BRANCHES

cfg, parts = load_config(), []
for acct, br in BRANCHES.items():
    raw = subprocess.run(["git", "show", f"origin/{br}:journal.db"], capture_output=True).stdout
    with tempfile.NamedTemporaryFile(suffix=".db", dir="/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/tmpx_inventory") as f:
        f.write(raw); f.flush()
        con = sqlite3.connect(f.name)
        x = pd.read_sql("SELECT strategy, symbol, side, date, entry_time, entry, stop, target, exit, exit_reason, meta, shares, pnl, "
                        "pnl_adj, r_multiple FROM trades WHERE run_id=1 AND exit_time IS NOT NULL", con); con.close()
    x["account"] = acct; parts.append(x)
t = pd.concat(parts, ignore_index=True)
t["date"] = t["date"].astype(str).str[:10]
t = t[t["date"] >= "2026-10-23"].copy()
t["r"] = cost_r_lr8(t, cfg).astype(float); t = t[t["r"].notna()]
t["k"] = t.strategy + "|" + t.symbol + "|" + t.date + "|" + t.entry_time.astype(str).str[:16]
t = t.drop_duplicates("k")
t["sidel"] = np.where(t.side > 0, "long", "short")
def summ(g):
    d = g.groupby("date")["r"].sum()
    se = d.std(ddof=1) / np.sqrt(len(d))
    return pd.Series({"tr": len(g), "sess": len(d), "R": g.r.sum(), "avgR": g.r.mean(), "day_t": d.mean() / se if se > 0 else np.nan,
                      "R_wo_best": g.r.sum() - d.max(), "green_days": int((d > 0).sum())})
print("All accounts, deduped:"); print(t.groupby("sidel").apply(summ).round(3).to_string())
print("\nNon-Graveyard:"); print(t[t.account != "graveyard"].groupby("sidel").apply(summ).round(3).to_string())
print("\nBy account x side (R, trades):")
p = t.pivot_table(index="account", columns="sidel", values="r", aggfunc=["sum", "count"]).round(1); print(p.to_string())
print("\nSince 11-19 (Epoch 1), non-Graveyard:"); print(t[(t.account != "graveyard") & (t.date >= "2026-11-19")].groupby("sidel").apply(summ).round(3).to_string())
lg = t[(t.sidel == "long") & (t.account != "graveyard")]
s = lg.groupby("strategy")["r"].agg(["count", "sum", "mean"]).sort_values("sum")
print(f"\nLong setups (non-GY): {len(s)}; positive total {int((s['sum']>0).sum())}; top 5:"); print(s.tail(5).round(2).to_string())
