# review_shorts_autopsy re-run: headline split, Primary SPY gap-up shorts, latch vs same-account-day random drop. Usage: PYTHONPATH=. python rv1.py SCRATCH (after live_load.py). Educational only - not financial advice.
import sys, numpy as np, pandas as pd
from datetime import datetime
D=sys.argv[1]
t=pd.read_parquet(f"{D}/live.parquet")
t=t[(t.account!="graveyard")&(t.date>="2026-10-23")&(t.date<="2026-11-27")].copy()
gd=t.strategy.str.contains("gapdn|gap-slope|GAPDN|gap_dn",regex=True)
t["fam"]=np.where(t.side>0,"long",np.where(gd,"gd","other"))
print("sessions",t.date.nunique())
for f,g in t.groupby("fam"):
    ds=g.groupby("date").r.sum(); x=g[g.date!="2026-11-25"]
    print(f, len(g), round(g.r.sum(),1), "1125:", (g.date=="2026-11-25").sum(), round(ds.get("2026-11-25",0),1),
          "share", round(ds.get("2026-11-25",0)/g.r.sum(),3), "ex1125 avg", round(x.r.mean(),4))
# Primary shorts by SPY gap
try:
    from mcf.data.priors import _bars,_client
    d=_bars(_client(),["SPY"],datetime.fromisoformat("2026-10-15T00:00:00+00:00"),datetime.fromisoformat("2026-11-28T00:00:00+00:00"),None,"sip").reset_index()
    d["date"]=pd.to_datetime(d.timestamp,utc=True).dt.date.astype(str); d=d.sort_values("date")
    d["gap"]=(d.open/d.close.shift(1)-1)*100; gap=d.set_index("date").gap
    p=t[(t.account=="primary")&(t.side<0)].copy(); p["sg"]=p.date.map(gap)
    up=p[p.sg>=0.5]
    print("Primary shorts total", len(p), round(p.r.sum(),1), "| SPY gap>=0.5:", len(up), round(up.r.sum(),1), up.date.nunique(), sorted(up.date.unique()))
    print(up.groupby("strategy").r.sum().round(1).to_dict())
    print(up.groupby("date").r.sum().round(1).to_dict())
except Exception as e: print("spy fail", e)
# latch random control
t["et"]=pd.to_datetime(t.entry_time.astype(str),utc=True,format="mixed"); t["xt"]=pd.to_datetime(t.exit_time.astype(str),utc=True,format="mixed")
t=t[t.account!="primary"].sort_values(["account","strategy","date","et"]).copy()
keep=np.ones(len(t),bool); pos={i:k for k,i in enumerate(t.index)}
for _,g in t.groupby(["account","strategy","date"]):
    et,xt,r=g.et.to_numpy(),g.xt.to_numpy(),g.r.to_numpy(); kept=[]
    for j in range(len(g)):
        if sum(r[k] for k in kept if xt[k]<=et[j])<=-2: keep[pos[g.index[j]]]=False
        else: kept.append(j)
t["keep"]=keep
rng=np.random.default_rng(7)
for f,g in t.groupby("fam"):
    nd=(~g.keep).sum(); act=-g[~g.keep].r.sum(); act_x=-g[(~g.keep)&(g.date!="2026-11-25")].r.sum()
    gx=g[g.date!="2026-11-25"]; ndx=((~gx.keep)).sum()
    # random: drop same number of lots within the same account-day (preserves day exposure)
    sims=[];simx=[]
    grp=[(gg.r.to_numpy(),(~gg.keep).sum(),dd) for (a,dd),gg in g.groupby(["account","date"])]
    for _ in range(1000):
        s=0;sx=0
        for r,k,dd in grp:
            if k: v=-r[rng.choice(len(r),k,replace=False)].sum(); s+=v; sx+= v if dd!="2026-11-25" else 0
        sims.append(s); simx.append(sx)
    sims=np.array(sims); simx=np.array(simx)
    print(f"latch {f}: dropped {nd} actual dR {act:.1f} | random same acct-day mean {sims.mean():.1f} pct {(sims<act).mean()*100:.0f} || ex1125 actual {act_x:.1f} random {simx.mean():.1f} pct {(simx<act_x).mean()*100:.0f}")
