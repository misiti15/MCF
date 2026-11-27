"""PYRAMID-S: pool all live closed trades (run 1) from the 10 journals, LR8 R. Educational only - not financial advice."""
import sqlite3, subprocess, os, sys
import pandas as pd
from mcf.config import load_config
from mcf.costs import cost_r_lr8
from mcf.research.shadow_calib import BRANCHES
D=sys.argv[1]; cfg=load_config(); parts=[]
for acct, br in BRANCHES.items():
    p=os.path.join(D,"j.db")
    r=subprocess.run(["git","show",f"origin/{br}:journal.db"],capture_output=True).stdout
    if not r: continue
    open(p,"wb").write(r)
    con=sqlite3.connect(p)
    x=pd.read_sql("SELECT strategy,symbol,side,date,entry_time,exit_time,entry,stop,target,exit,exit_reason,meta,shares,pnl,pnl_adj,r_multiple FROM trades WHERE run_id=1 AND exit_time IS NOT NULL",con)
    con.close(); os.remove(p); x["account"]=acct; parts.append(x); print(acct,len(x))
t=pd.concat(parts,ignore_index=True); t["date"]=t["date"].astype(str).str[:10]
t["r"]=cost_r_lr8(t,cfg).astype(float); t=t[t.r.notna()]
t["k"]=t.strategy+"|"+t.symbol+"|"+t.date+"|"+t.entry_time.astype(str).str[:16]
t["dup"]=t.duplicated("k")
t.drop(columns=["target"]).to_pickle(os.path.join(D,"all.pkl"))
print(len(t), (~t.dup).sum(), t.date.min(), t.date.max())
