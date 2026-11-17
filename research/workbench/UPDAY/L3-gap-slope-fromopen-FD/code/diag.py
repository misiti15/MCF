from load3 import *
import sim3, pandas as pd, numpy as np
pd.set_option("display.width",250)
T={n:run(v) for n,v in (("PARENT",sim3.BASE),("WB4",sim3.WB4))}
pd.to_pickle(T,"diag_trades.pkl")
for n,o in T.items():
    for k,t in o.items():
        g=t.groupby("dtype").r.agg(["size","mean","sum"]); g["days"]=t.groupby("dtype").date.nunique()
        nd=pd.Series(DAYS[k]).map(DT.dtype).value_counts(); g["test_days"]=nd
        print(n,k); print(g.round(3).to_string())
for n in ("PARENT","WB4"):
  for k in ("replay","2y"):
    t=T[n][k].copy()
    t["b950"]=pd.cut(t.spy950,[-9,-0.5,-0.25,0,0.15,0.3,0.5,9])
    t["b30"]=pd.cut(t.spy30,[-9,-0.2,-0.1,0,0.1,0.2,9])
    t["brs"]=pd.cut(t.rs950,[-99,0,2,4,6,99])
    t["btod"]=pd.cut(t.tod,[900,1030,1100,1200,1300,1600])
    t["bgap"]=pd.cut(t.gap,[-99,-8,-5,-4,-3.2,0])
    for b in ("b950","b30","brs","btod","bgap"):
        x=t.pivot_table(index=b,columns="dtype",values="r",aggfunc=["mean","size"],observed=True)
        print(f"== {n} {k} by {b}"); print(x.round(3).to_string())
    # how well does U predict full-day up
    for thr in (0.15,0.25,0.4):
        u=t.spy950>thr; print(n,k,"spy950>",thr,"share of trades",round(u.mean(),3),"P(up day|U)",round((t.dtype[u]=="up").mean(),3),"avgR U",round(t.r[u].mean(),3),"not U",round(t.r[~u].mean(),3))
