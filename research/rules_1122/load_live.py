"""Live journals (run 1, closed trades) of every mcf-data* branch with entry/exit times, LR8 cost-R (mcf.costs.cost_r_lr8).
Duplicates (identical setup|symbol|date|entry minute across accounts) are flagged, not dropped (dup=True on later accounts).
Usage: python load_live.py CHECKOUT OUT.parquet.  Educational only - not financial advice."""
import sqlite3, subprocess, sys, tempfile
import pandas as pd
CK, OUT = sys.argv[1], sys.argv[2]
sys.path.insert(0, CK)
from mcf.config import load_config
from mcf.costs import cost_r_lr8
from mcf.research.shadow_calib import BRANCHES
cfg, parts = load_config(), []
for acct, br in BRANCHES.items():
    raw = subprocess.run(["git", "-C", CK, "show", f"origin/{br}:journal.db"], capture_output=True).stdout
    if not raw:
        print("missing", br); continue
    with tempfile.NamedTemporaryFile(suffix=".db") as f:
        f.write(raw); f.flush()
        con = sqlite3.connect(f.name)
        x = pd.read_sql("SELECT id, strategy, symbol, side, date, entry_time, exit_time, entry, stop, target, exit, exit_reason, "
                        "meta, shares, pnl, pnl_adj, r_multiple FROM trades WHERE run_id=1 AND exit_time IS NOT NULL", con)
        con.close()
    x["account"] = acct
    parts.append(x)
t = pd.concat(parts, ignore_index=True)
t["date"] = t["date"].astype(str).str[:10]
t["r"] = cost_r_lr8(t, cfg).astype(float)
t = t[t["r"].notna()].copy()
t["k"] = t["strategy"] + "|" + t["symbol"] + "|" + t["date"] + "|" + t["entry_time"].astype(str).str[:16]
t["dup"] = t.duplicated("k")
t["side"] = t["side"].map(lambda s: 1 if str(s).lower() in ("1", "long", "buy") else -1)
t = t.drop(columns=["meta"])
t.to_parquet(OUT, index=False)
print(t.shape, t.groupby("account").size().to_dict(), "dups", int(t.dup.sum()))
print(t.date.min(), t.date.max())
