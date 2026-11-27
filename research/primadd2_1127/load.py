"""PRIMADD2-1127: load live (run 1) + PSHADOW (run 3) closed trades from the mcf-data* journals, LR8 (cost_r_lr8) and booked R. Usage: python load.py REPO DATADIR OUT.pkl. Educational only - not financial advice."""
import sys,sqlite3,pandas as pd,os
W=sys.argv[1]; D=sys.argv[2]; sys.path.insert(0,W); os.chdir(W)
from mcf.config import load_config
from mcf.costs import cost_r_lr8
ACC={'primary':'mcf-data','testing':'mcf-data-testing','testing2':'mcf-data-testing2','graveyard':'mcf-data-graveyard','livelab':'mcf-data-livelab','explore1':'mcf-data-explore1','testingd':'mcf-data-testingd','testinge':'mcf-data-testinge','testingf':'mcf-data-testingf','gen':'mcf-data-gen'}
cfg=load_config(); parts=[]
for a,b in ACC.items():
    con=sqlite3.connect(f"{D}/{b}/journal.db")
    x=pd.read_sql("SELECT run_id,strategy,symbol,side,date,entry_time,exit_time,entry,stop,target,exit,exit_reason,meta,shares,pnl,pnl_adj,r_multiple FROM trades WHERE run_id in (1,3) AND exit_time IS NOT NULL",con)
    con.close(); x['account']=a; parts.append(x)
t=pd.concat(parts,ignore_index=True); t['date']=t.date.astype(str).str[:10]
t['r']=cost_r_lr8(t,cfg).astype(float)
risk=(t.entry-t.stop).abs()*t.shares.abs()
t['r_booked']=t.pnl_adj/risk.where(risk>0)
t=t[t.r.notna()]
t['k']=t.strategy+'|'+t.symbol+'|'+t.date+'|'+t.entry_time.astype(str).str[:16]+'|'+t.run_id.astype(str)
t.to_pickle(sys.argv[3]); print(len(t), t.date.max(), t.groupby(['run_id']).size().to_dict())
