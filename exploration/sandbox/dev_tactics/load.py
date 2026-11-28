"""Read-only loader: closed live trades (run 1) of all 10 journals, LR8 R after costs. Journal copies are passed as a
directory of <branch>.db files (git show origin/<branch>:journal.db). Educational only - not financial advice."""
import sqlite3, sys
from pathlib import Path
import pandas as pd
from mcf.config import load_config
from mcf.costs import cost_r_lr8
from mcf.research.shadow_calib import BRANCHES

def load(dbdir, dedupe=True):
    cfg, parts = load_config(), []
    for acct, br in BRANCHES.items():
        p = Path(dbdir) / f"{br}.db"
        if not p.exists():
            continue
        con = sqlite3.connect(p)
        x = pd.read_sql("SELECT strategy, symbol, side, date, entry_time, entry, stop, target, exit, exit_reason, meta, "
                        "shares, pnl, pnl_adj, r_multiple, mae_r, mfe_r FROM trades WHERE run_id=1 AND exit_time IS NOT NULL", con)
        con.close()
        x["account"] = acct
        parts.append(x)
    t = pd.concat(parts, ignore_index=True)
    t["date"] = t["date"].astype(str).str[:10]
    t["r"] = cost_r_lr8(t, cfg).astype(float)
    t = t[t["r"].notna()].copy()
    t["k"] = t["strategy"] + "|" + t["symbol"] + "|" + t["date"] + "|" + t["entry_time"].astype(str).str[:16]
    t["gross"] = t["r_multiple"].astype(float)
    if dedupe:
        t = t.drop_duplicates("k")
    return t.reset_index(drop=True)

def signals(dbdir):
    parts = []
    for acct, br in BRANCHES.items():
        p = Path(dbdir) / f"{br}.db"
        if not p.exists():
            continue
        con = sqlite3.connect(p)
        x = pd.read_sql("SELECT day, ts, symbol, strategy, side, status, reason FROM signals WHERE run_id=1", con)
        con.close()
        x["account"] = acct
        parts.append(x)
    return pd.concat(parts, ignore_index=True)
