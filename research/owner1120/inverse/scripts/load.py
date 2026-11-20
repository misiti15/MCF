"""Load live (run 1, all accounts, LR8 costs) + run-2 what-ifs + signals, and the 2-year lab fires. Research only."""
import sys, sqlite3, pandas as pd, numpy as np
WT='/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/rules1119'
W='/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/inv1120_tmp'
sys.path.insert(0,WT); sys.path.insert(0,WT+'/research/owner1120/inverse')
from mcf.costs import with_cost_r
import shadow as S
rows=[];sig=[];wi=[]
for a,b in S.BRANCHES.items():
    c=sqlite3.connect(f'{W}/{b}.db')
    t=pd.read_sql("select * from trades where run_id=1 and exit is not null and pnl_adj is not null and shares>0 and entry!=stop",c)
    t=with_cost_r(t); t['acct']=a; rows.append(t)
    s=pd.read_sql("select day,symbol,strategy,side,status,reason from signals where run_id=1",c); s['acct']=a; sig.append(s)
    w=pd.read_sql("select strategy,symbol,side,date,r_multiple,meta from trades where run_id=2 and r_multiple is not null",c); w['acct']=a; wi.append(w)
T=pd.concat(rows,ignore_index=True); T['R']=T.r_multiple.astype(float)
T=T[['acct','strategy','symbol','side','date','R','entry_time']].copy()
T.to_pickle(f'{W}/live.pkl'); pd.concat(sig).to_pickle(f'{W}/sig.pkl'); pd.concat(wi).to_pickle(f'{W}/wi.pkl')
print('live',len(T),T.date.min(),T.date.max(),T.groupby('acct').size().to_dict())
L=pd.read_parquet(WT+'/research/rootcause_1119/sl_work/family_trades.parquet'); L['date']=L.date.astype(str)
assert not L.date.between(S.LOCK_A,S.LOCK_B).any()
L=L.rename(columns={'r':'R'}); L['side']=np.where(L.side=='short',-1,1); L['strategy']=L.setup; L['acct']='lab'
L[['acct','strategy','symbol','side','date','R','tod']].to_pickle(f'{W}/lab.pkl'); print('lab',len(L),L.date.min(),L.date.max())
