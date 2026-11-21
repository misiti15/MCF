import sys, numpy as np, pandas as pd
sys.path.insert(0,"/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/fp/cap-etp")
import engine as E, run as R
W="/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/fp/cap-etp/"
F=E.load("T1"); C=E.compass(F); SD=R.spyday(F)
cfg=[c for c in R.CFGS if c["name"]=="A-vwhold-t1s1"][0]
ft=pd.read_parquet(W+"fit_trades_r1.parquet"); ft=ft[ft.cfg=="A-vwhold-t1s1"]
ck=pd.read_parquet(W+"check_A-vwhold-t1s1.parquet")
for nm,t in (("fit",ft),("check",ck)):
    day=t.groupby("date").r.sum()
# state-matched null: same date+symbol, random tod in DN-state 950..1300, ETP above its open (no vwhold)
x=F[F.symbol.isin(E.INV)].merge(C[["date","tod","state"]],on=["date","tod"])
x=x[(x.state==-2)&x.tod.between(950,1300)&(x.atr_d>0)]
for nm,t in (("fit",ft),("check",ck)):
    rng=np.random.default_rng(3); outs=[];outs2=[]
    g=x.set_index(["symbol","date"]).sort_index()
    for d in range(10):
        rows=[];rows2=[]
        for r in t.itertuples():
            try: c=g.loc[(r.symbol,r.date)]
            except KeyError: continue
            if isinstance(c,pd.Series): c=c.to_frame().T
            rows.append(dict(c.iloc[rng.integers(len(c))],symbol=r.symbol,date=r.date))
            c2=c[c.fo>0]
            if len(c2): rows2.append(dict(c2.iloc[rng.integers(len(c2))],symbol=r.symbol,date=r.date))
        res=[]
        for rr in (rows,rows2):
            h=pd.DataFrame(rr)
            Rk=0.25*h.atr_d.to_numpy().astype(float); e=h.close.to_numpy().astype(float)
            sig=pd.DataFrame({"symbol":h.symbol.values,"date":h.date.values,"tod":h.tod.values.astype(int),"side":1,"entry":e,"stop":e-Rk,"tgt":e+Rk,"risk":Rk,"gap":h.gap.fillna(0).astype(float).values,"adv20":h.adv20.values})
            b=E.book(E.add_r(E.walk(sig,R.bars_for("T1",sig.symbol.unique()))))
            res.append(b[['date','r']])
        outs.append(res[0]); outs2.append(res[1])
    N=pd.concat(outs2).groupby("date").r.mean(); A=t.groupby("date").r.mean()
    d=(A-N).dropna(); import math
    print(nm,"paired per-day diff (actual - ETP-above-open null)",round(d.mean(),4),"t",round(d.mean()/(d.std()/math.sqrt(len(d))),2),"days",len(d),"days diff>0",round((d>0).mean(),2))
    N0=pd.concat(outs).groupby("date").r.mean(); d0=(A-N0).dropna()
    print(nm,"paired vs random-DN-tod null",round(d0.mean(),4),"t",round(d0.mean()/(d0.std()/math.sqrt(len(d0))),2))
    continue
    print(nm,"actual",round(t.r.mean(),4),"state-matched null (same date/sym, random DN tod)",round(np.mean(outs),4),"sd",round(np.std(outs),4),
      "| +ETP-above-open null",round(np.mean(outs2),4),"sd",round(np.std(outs2),4),"pct>",np.mean(np.array(outs2)<t.r.mean()))
