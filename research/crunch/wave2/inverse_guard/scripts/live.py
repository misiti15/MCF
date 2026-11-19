import sys,sqlite3,pandas as pd,numpy as np,re
WT='/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/rules1119'
W='/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/ig_tmp'
sys.path.insert(0,WT); sys.path.insert(0,WT+'/research/forward/compass_gate')
from mcf.costs import with_cost_r
import shadow as S
rows=[];sk=[];wi=[]
for a,b in S.BRANCHES.items():
    c=sqlite3.connect(f'{W}/{b}.db')
    t=pd.read_sql("select * from trades where run_id=1 and exit is not null and pnl_adj is not null and shares>0 and entry!=stop",c)
    t=with_cost_r(t); t['acct']=a; rows.append(t)
    s=pd.read_sql("select day,symbol,strategy,side,status,reason,run_id from signals where side=-1",c); s['acct']=a; sk.append(s)
    w=pd.read_sql("select * from trades where run_id=2 and side=-1 and meta like '%not shortable/ETB%' and r_multiple is not null",c); w['acct']=a; wi.append(w)
T=pd.concat(rows,ignore_index=True); T['R']=T.r_multiple
T[['acct','strategy','symbol','side','date','R']].to_pickle(f'{W}/live.pkl')
pd.concat(sk).to_pickle(f'{W}/sig.pkl'); pd.concat(wi)[['acct','strategy','symbol','date','r_multiple']].to_pickle(f'{W}/wi.pkl')
print(len(T),T.date.min(),T.date.max(),T.groupby('acct').size().to_dict())
