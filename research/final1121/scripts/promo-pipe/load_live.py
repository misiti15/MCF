import sqlite3, subprocess, tempfile, sys
import pandas as pd
sys.path.insert(0, '/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/inbox')
from mcf.config import load_config
from mcf.costs import cost_r_lr8
from mcf.research.shadow_calib import BRANCHES
cfg=load_config(); parts=[]
for acct, br in BRANCHES.items():
    raw=subprocess.run(["git","-C","/home/user/MCF","show",f"origin/{br}:journal.db"],capture_output=True).stdout
    if not raw: print('miss',acct); continue
    with tempfile.NamedTemporaryFile(suffix=".db") as f:
        f.write(raw); f.flush(); con=sqlite3.connect(f.name)
        x=pd.read_sql("SELECT strategy, symbol, side, date, entry_time, exit_time, entry, stop, shares, pnl, pnl_adj, r_multiple FROM trades WHERE run_id=1 AND exit_time IS NOT NULL",con)
        con.close()
    x['account']=acct; parts.append(x)
t=pd.concat(parts,ignore_index=True)
t['date']=t['date'].astype(str).str[:10]
t['r']=cost_r_lr8(t,cfg).astype(float)
t=t[t.r.notna()]
t['k']=t.strategy+'|'+t.symbol+'|'+t.date+'|'+t.entry_time.astype(str).str[:16]
t=t.drop_duplicates('k').reset_index(drop=True)
t.to_pickle(sys.argv[1]); print(t.shape, t.date.max()); print(t.groupby('account').size())
