import pandas as pd,numpy as np
t=pd.read_pickle("t.pkl"); t=t[t.date<"2026-11-04"]
t=t.sort_values("entry_time").drop_duplicates(["strategy","symbol","date","entry_time"])
t["sf"]=(t.entry-t.stop).abs()/t.entry          # stop distance as fraction of price
g=t.groupby("strategy").R.agg(["count","mean","std"]); g=g[g["count"]>=20]
g["shrunk"]=g["mean"]*g["count"]/(g["count"]+20)
# per-setup day totals and day-type split using SPY proxy: use primary history? approximate day type by sign of the account-wide short book is circular; use SPY from repo cache if present
top5=g.sort_values("shrunk",ascending=False).head(5).index.tolist()
print(g.loc[top5].round(3))
x=t[t.strategy.isin(top5)].copy()
days=sorted(x.date.unique()); print("sessions",len(days),days[0],days[-1])
print("median stop distance %.2f%% of price"%(100*x.sf.median()))
def sim(f,bp_mult,cap=100000):
    eq=cap; out=[]
    for d in days:
        g=x[x.date==d].sort_values("entry_time"); open_=[]; pnl=0;n=0
        for r in g.itertuples():
            open_=[(e,nv) for e,nv in open_ if e>r.entry_time]
            risk=f*eq; notional=risk/max(r.sf,1e-4)
            if sum(nv for _,nv in open_)+notional>bp_mult*eq: continue
            open_.append((r.exit_time,notional)); pnl+=r.R*risk; n+=1
        eq+=pnl; out.append((d,n,pnl,eq))
    s=pd.DataFrame(out,columns=["d","n","pnl","equity"])
    e=pd.concat([pd.Series([cap]),s.equity]); dd=((e-e.cummax())/e.cummax()).min()
    return s, s.equity.iloc[-1]/cap-1, dd, (s.pnl>0).mean(), s.pnl.max()/max(s.pnl.sum(),1e-9)
print("\nrisk/trade  BP   return  maxDD  green%  bestday share  trades")
for bp in (1,4):
  for f in (0.0025,0.005,0.01,0.02,0.03):
    s,ret,dd,gr,bs=sim(f,bp)
    print(f"{f*100:5.2f}%   {bp}x  {ret*100:7.1f}% {dd*100:6.1f}% {gr*100:5.0f}%  {bs*100:5.0f}%   {s.n.sum()}")
# Kelly on daily R of the 5-setup book per unit risk
dR=x.groupby("date").R.sum().reindex(days,fill_value=0)
print("\ndaily book R: mean %.2f sd %.2f; Kelly f per-R unit = %.4f; w/o best day mean %.2f"%(dR.mean(),dR.std(),dR.mean()/dR.var(),(dR.sum()-dR.max())/(len(dR)-1)))
print("\nfiner grid, 4x BP")
for f in (0.001,0.0015,0.002,0.0025,0.003,0.004):
    s,ret,dd,gr,bs=sim(f,4); print(f"{f*100:5.2f}%  {ret*100:6.1f}% DD {dd*100:5.1f}% green {gr*100:3.0f}% trades {s.n.sum()} w/o best day {100*(s.pnl.sum()-s.pnl.max())/100000:5.1f}%")
