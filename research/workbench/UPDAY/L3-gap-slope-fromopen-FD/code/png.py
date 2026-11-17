import pandas as pd, numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
x=pd.concat([pd.read_csv(f"res_ROUND{i}.csv") for i in (1,2,3,4)]).drop_duplicates(["cfg","test"]).set_index(["cfg","test"])
C={"PARENT":("Parent","#2a78d6"),"R2d Y1 + U15 entries end 12:00":("WB5 (up-day copy of parent)","#eb6834"),
   "WB4":("WB4","#1baf7a"),"V2 WB4 + U15: no entries before 11:00":("WB4 + up-state: no entries before 11:00","#eda100")}
plt.rcParams.update({"font.size":10,"axes.spines.top":False,"axes.spines.right":False})
fig,ax=plt.subplots(1,2,figsize=(12,4.6))
for a,test,tt in ((ax[0],"replay","Session replay (10-12..11-12, 23 sessions)"),(ax[1],"2y","2-year backtest (locked block excluded)")):
    for i,(k,(lab,col)) in enumerate(C.items()):
        vals=[x.loc[(k,test),f"avg_{d}"] for d in ("up","down","quiet")]
        xs=np.arange(3)+(i-1.5)*0.2
        a.bar(xs,vals,0.18,color=col,label=lab,edgecolor="white",linewidth=1)
        for xx,v in zip(xs,vals): a.text(xx,v+(0.01 if v>=0 else -0.03),f"{v:+.2f}",ha="center",fontsize=7,color="#333")
    a.axhline(0,color="#888",lw=0.8); a.set_xticks(range(3)); a.set_xticklabels(["Up days","Down days","Quiet days"])
    a.set_title(tt,fontsize=10); a.set_ylabel("avg R per trade after costs"); a.grid(axis="y",color="#eee")
ax[0].legend(fontsize=8,frameon=False,loc="upper left")
fig.suptitle("L3 Gap-Down Recovery Fade: R per trade by day type (SPY 09:50 close -> 16:00, ±0.25%) - Educational only, not financial advice",fontsize=10)
fig.tight_layout(); fig.savefig("L3-upday_daytype.png",dpi=130)
T={}
for r in (1,4): T.update(pd.read_pickle(f"trades_ROUND{r}.pkl"))
T.update({k:v for k,v in pd.read_pickle("trades_ROUND2.pkl").items()})
fig,ax=plt.subplots(1,2,figsize=(12,4.4))
for a,test in ((ax[0],"replay"),(ax[1],"2y")):
    for k,(lab,col) in C.items():
        t=T[k][test]; d=t.groupby("date").r.sum().sort_index().cumsum()
        a.plot(pd.to_datetime(d.index),d.values,color=col,lw=2,label=lab)
    a.axhline(0,color="#888",lw=0.8); a.set_ylabel("cumulative R after costs"); a.grid(color="#eee")
    a.set_title("Session replay" if test=="replay" else "2-year backtest",fontsize=10)
ax[0].legend(fontsize=8,frameon=False); fig.autofmt_xdate()
fig.suptitle("Equity curves, parent / WB5 / WB4 / WB4 up-state variant - Educational only, not financial advice",fontsize=10)
fig.tight_layout(); fig.savefig("L3-upday_curves.png",dpi=130)
