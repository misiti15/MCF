"""L3: extended live trades (run 1, all 10 accounts, LR8), dedup like footrace.live_trades, keeps side/times/meta.
Educational only - not financial advice."""
import os, sqlite3, subprocess, sys
import pandas as pd
INBOX = sys.argv[1]
sys.path.insert(0, INBOX)
from mcf.config import load_config
from mcf.costs import cost_r_lr8
from mcf.research.shadow_calib import BRANCHES
cfg = load_config(); parts = []
tmp = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_j.db")
for acct, br in BRANCHES.items():
    raw = subprocess.run(["git", "-C", INBOX, "show", f"origin/{br}:journal.db"], capture_output=True).stdout
    if not raw: print("missing", acct); continue
    open(tmp, "wb").write(raw)
    con = sqlite3.connect(tmp)
    x = pd.read_sql("SELECT * FROM trades WHERE run_id=1 AND exit_time IS NOT NULL", con); con.close(); os.remove(tmp)
    x["account"] = acct; parts.append(x); print(acct, len(x))
t = pd.concat(parts, ignore_index=True)
t["date"] = t["date"].astype(str).str[:10]
t["r"] = cost_r_lr8(t, cfg).astype(float)
t = t[t["r"].notna()]
t["k"] = t["strategy"] + "|" + t["symbol"] + "|" + t["date"] + "|" + t["entry_time"].astype(str).str[:16]
t = t.drop_duplicates("k").reset_index(drop=True)
keep = [c for c in ["account","strategy","symbol","side","date","entry_time","exit_time","entry","stop","target","exit","exit_reason","shares","r","r_multiple","meta"] if c in t]
t[keep].to_pickle("live_ext.pkl"); print(t.shape, t.date.min(), t.date.max())
