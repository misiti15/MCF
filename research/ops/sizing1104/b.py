import pandas as pd,numpy as np
t=pd.read_pickle("t.pkl")
top=["MF2-open-rsimidhi-flowsell-FD","RW5-heat30-flowsell-rsi5pop-gapdn-short-FD","RW3-gapdn-rsi5pop-flowsell-short-FD"]
days=['2026-10-22','2026-10-23','2026-10-26','2026-10-27','2026-10-28','2026-10-29','2026-10-30','2026-11-02','2026-11-03']
x=t[t.strategy.isin(top)&t.date.isin(days)].copy()
print(x.groupby(["strategy","acct"]).size())
x=x.sort_values("entry_time").drop_duplicates(["strategy","symbol","date","entry_time"])
x["ret"]=x.pnl_adj/(x.entry*x.shares)       # return on notional after costs
x["notional_actual"]=x.entry*x.shares
CAP=100000; POS=0.25*CAP
x["pnl25"]=x.ret*POS
print("actual avg notional $%.0f"%x.notional_actual.mean())
def sim(maxpos):
    rows=[]
    for d,g in x.groupby("date"):
        open_=[];taken=[]
        for _,r in g.sort_values("entry_time").iterrows():
            open_=[e for e in open_ if e>r.entry_time]
            if maxpos is None or len(open_)<maxpos:
                open_.append(r.exit_time); taken.append(r)
        tk=pd.DataFrame(taken)
        rows.append(dict(date=d,trades=len(tk),R=tk.R.sum(),pnl=tk.pnl25.sum(),pnl_actual=tk.pnl_adj.sum(),win=(tk.R>0).mean()))
    return pd.DataFrame(rows)
for mp,lab in [(None,"no limit (needs margin)"),(16,"<=16 open (4x intraday BP)"),(4,"<=4 open (no margin)")]:
    s=sim(mp)
    print("\n==",lab); print(s.round(2).to_string(index=False))
    print("TOTAL trades %d  R %.1f  avgR %.3f  P/L $%.0f  green days %d/9  worst day $%.0f  best day $%.0f  w/o best day $%.0f"%(
        s.trades.sum(),s.R.sum(),s.R.sum()/s.trades.sum(),s.pnl.sum(),(s.pnl>0).sum(),s.pnl.min(),s.pnl.max(),s.pnl.sum()-s.pnl.max()))
    eq=CAP+s.pnl.cumsum(); dd=(eq-eq.cummax()).min(); print("max drawdown $%.0f"%dd)
# per setup
x["d"]=x.date
print(x.groupby("strategy").agg(n=("R","size"),avgR=("R","mean"),R=("R","sum"),pnl25=("pnl25","sum")).round(3))
# concurrency
mx=0
for d,g in x.groupby("date"):
    ev=sorted([(r.entry_time,1) for r in g.itertuples()]+[(r.exit_time,-1) for r in g.itertuples()])
    c=0
    for _,v in ev: c+=v; mx=max(mx,c)
print("max concurrent positions",mx)
