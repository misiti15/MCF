import sqlite3, subprocess, tempfile, sys, pandas as pd
R='/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/inbox'
sys.path.insert(0,R)
from mcf.config import load_config
from mcf.costs import cost_r_lr8
from mcf.research.shadow_calib import BRANCHES
cfg=load_config(); parts=[]
for acct, br in BRANCHES.items():
    raw=subprocess.run(["git","-C",R,"show",f"origin/{br}:journal.db"],capture_output=True).stdout
    if not raw: print('none',acct); continue
    with tempfile.NamedTemporaryFile(suffix=".db") as f:
        f.write(raw); f.flush(); con=sqlite3.connect(f.name)
        x=pd.read_sql("SELECT strategy, symbol, side, date, signal_time, entry_time, entry, stop, target, exit_time, exit, exit_reason, shares, pnl, pnl_adj, r_multiple, mfe_r, mae_r FROM trades WHERE run_id=1 AND exit_time IS NOT NULL",con); con.close()
    x['account']=acct; parts.append(x)
t=pd.concat(parts,ignore_index=True); t['date']=t.date.astype(str).str[:10]
t['r']=cost_r_lr8(t,cfg).astype(float)
print(t.date.max())
t.to_parquet('live_all.parquet')
e=t[t.strategy.str.contains('ETF')]
print(e[e.date>='2026-11-16'].groupby(['date','account','strategy']).agg(n=('r','size'),R=('r','sum')))
