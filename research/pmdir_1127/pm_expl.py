import sys, numpy as np, pandas as pd
sys.path.insert(0,__import__('os').path.dirname(__file__)); sys.path.insert(0,__import__('os').path.dirname(__file__)+'/../..')
import pm_score as P
df=pd.read_csv(sys.argv[1]).dropna(subset=P.NUM).reset_index(drop=True)
for f in ['qi','gap']:
    for s in ['EARLY','T2','FIT','CHECK']:
        d=df[df.split==s].reset_index(drop=True); side=np.where(d[f]>0,1,-1)
        hit=((side==1)==(d.y==1)).mean()
        g,rl,r8,_=P.trade(d,side)
        print(f,s,len(d),'hit',round(hit,3),'base',round(d.y.mean(),3),'g',round(g.mean(),3),'L',round(rl.mean(),3),'t',round(P.tstat(rl),2),'lr8',round(r8.mean(),3),'bp',round((side*d.ret_pm).mean()*1e4,2))
