import sys
import pandas as pd, numpy as np
from sklearn.metrics import roc_auc_score
df=pd.read_csv(sys.argv[1]).dropna()
F=["mret","mrange","vwap","breadth","rvm","rv20","qi","prev","gap","lmom","w60","dow"]
rows=[]
for f in F:
    r={'f':f}
    for s in ['EARLY','T2','FIT','CHECK']:
        d=df[df.split==s]; r[s]=round(roc_auc_score(d.y,d[f]),3)
    rows.append(r)
print(pd.DataFrame(rows).to_string())
# conditional: afternoon up-rate by morning return tercile and by mret sign with |mret|>0.5%
for s in ['EARLY','T2','FIT','CHECK']:
    d=df[df.split==s]
    big=d[abs(d.mret)>0.005]
    print(s,'n',len(d),'up',round(d.y.mean(),3),'big n',len(big),'follow',round(((big.mret>0)==(big.y==1)).mean(),3),
      'pm|ret| bp',round(d.ret_pm.abs().mean()*1e4,1))
