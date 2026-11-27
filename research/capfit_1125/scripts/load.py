import sqlite3, subprocess, os, sys
import pandas as pd
from mcf.config import load_config
from mcf.costs import cost_r_lr8
from mcf.research.shadow_calib import BRANCHES
D = sys.argv[1]
cfg, parts = load_config(), []
for acct, br in BRANCHES.items():
    p = os.path.join(D, "j.db")
    r = subprocess.run(["git","show",f"origin/{br}:journal.db"],capture_output=True).stdout
    if not r: print('missing',acct); continue
    open(p,"wb").write(r)
    con = sqlite3.connect(p)
    x = pd.read_sql("SELECT strategy, symbol, side, date, entry_time, exit_time, entry, stop, target, exit, exit_reason, meta, shares, pnl, pnl_adj, r_multiple FROM trades WHERE run_id=1 AND exit_time IS NOT NULL", con)
    x["account"]=acct; parts.append(x); con.close(); os.remove(p)
t = pd.concat(parts, ignore_index=True)
t["date"]=t["date"].astype(str).str[:10]
t["r"]=cost_r_lr8(t,cfg).astype(float)
t=t[t["r"].notna()]
t["k"]=t["strategy"]+"|"+t["symbol"]+"|"+t["date"]+"|"+t["entry_time"].astype(str).str[:16]
n0=len(t); t=t.drop_duplicates("k")
print(n0,len(t))
t[["account","strategy","symbol","side","date","entry_time","exit_time","exit_reason","entry","stop","exit","r_multiple","r"]].to_parquet(os.path.join(D,"all_trades.parquet"))
print(len(t), t.r.sum(), t.date.nunique(), t.date.min(), t.date.max())
