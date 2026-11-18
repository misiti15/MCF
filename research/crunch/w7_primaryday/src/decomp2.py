import pandas as pd,numpy as np
t=pd.read_pickle('t2.pkl')
DR=t.groupby('date').R.sum(); t['gd']=t.date.map(DR>0)
for col in ['clu','side','stack','stack_same_setup','sym_prior_loss','sym_prior_stop','exit_reason']:
    k=t[col].clip(upper=3) if pd.api.types.is_numeric_dtype(t[col]) else t[col]
    x=t.assign(k=k).groupby(['k','gd']).R.agg(['size','mean','sum']).round(3)
    print('##',col); print(x.unstack().to_string())
t['ob']=pd.cut(t.open_same_side,[-1,2,5,10,20,100])
print(t.groupby('ob',observed=True).R.agg(['size','mean','sum']).round(3))
t['sq']=pd.cut(t.spy_move,[-9,-0.3,-0.1,0.1,0.3,9])
print('spy move with trade');print(t.groupby(['side','sq'],observed=True).R.agg(['size','mean','sum']).round(3).to_string())
t['sfo']=pd.cut(t.spy_e_fo*t.side,[-9,-0.5,-0.2,0,0.2,0.5,9])
print('SPY from open at entry x side (+ = market already moving trade way)');print(t.groupby(['sfo'],observed=True).R.agg(['size','mean','sum']).round(3).to_string())
print(t.groupby(['strategy','gd']).R.sum().unstack().round(1).to_string())
