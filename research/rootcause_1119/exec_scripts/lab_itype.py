import glob, sys, pandas as pd, numpy as np
sys.argv=[sys.argv[0]]
exec(open('exec_scripts/itype.py').read())
fs=sorted(glob.glob('/home/user/MCF/research/history2y/data/bt_lab1104/sig_*.parquet'))
d=pd.concat([pd.read_parquet(f) for f in fs]); 
d=d[d.setup.isin(['L3-gap-slope-fromopen-FD','ST7-rsi50dn-long-pm-t1s1-FD'])]
d=d[~d.date.between('2024-11-01','2025-02-28')]
d['itype']=d.symbol.map(itype)
def exbest(x):
    day=x.groupby('date').r.sum(); b=day.idxmax(); rest=x[x.date!=b]
    return pd.Series(dict(n=len(x),days=x.date.nunique(),tot=x.r.sum(),avg=x.r.mean(),win=(x.r>0).mean(),avg_wo_best=rest.r.mean(),best_share=day.max()/x.r.sum() if x.r.sum()>0 else np.nan,stop_share=(x.kind==1).mean()))
print(d.groupby(['setup','itype']).apply(exbest).round(3).to_string())
print(d.groupby('setup').apply(exbest).round(3).to_string())
print(d.kind.value_counts())
d.to_pickle('exec_data/lab2y.pkl')
