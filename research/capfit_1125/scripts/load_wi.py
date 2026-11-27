import sqlite3, subprocess, sys, os
import pandas as pd
sys.path.insert(0,'.')
from mcf.research.shadow_calib import BRANCHES
D=sys.argv[1]; S=[l.strip() for l in open(D+'/setups.csv')]
parts=[]
for acct, br in BRANCHES.items():
    raw = subprocess.run(["git","show",f"origin/{br}:journal.db"],capture_output=True).stdout
    p=D+'/w.db'; open(p,'wb').write(raw)
    con=sqlite3.connect(p)
    rid=[r[0] for r in con.execute("select id from runs where kind='whatif'")]
    if rid:
        q=",".join("'%s'"%s for s in S)
        x=pd.read_sql(f"SELECT strategy, symbol, side, date, entry_time, exit_time, entry, stop, exit, exit_reason, r_multiple, meta FROM trades WHERE run_id={rid[0]} AND strategy IN ({q})",con)
        x['why']=x.meta.str.extract(r"why=(.*)$")[0].fillna(''); x['account']=acct
        print(acct, x.why.str.replace(r"[\d\.\-]+","#",regex=True).value_counts().head(8).to_dict())
        parts.append(x.drop(columns=['meta']))
    con.close(); os.remove(p)
t=pd.concat(parts,ignore_index=True); t['date']=t.date.astype(str).str[:10]
t.to_parquet(D+'/whatif.parquet'); print(t.shape)
