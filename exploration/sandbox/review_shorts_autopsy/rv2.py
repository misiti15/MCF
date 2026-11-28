# review_shorts_autopsy: latch vs random drop of the same lot count in the same account on any day. Usage: python rv2.py SCRATCH rv1.py. Educational only - not financial advice.
import sys, numpy as np, pandas as pd
exec(open(sys.argv[2]).read().split("# Primary shorts by SPY gap")[0])
t["et"]=pd.to_datetime(t.entry_time.astype(str),utc=True,format="mixed"); t["xt"]=pd.to_datetime(t.exit_time.astype(str),utc=True,format="mixed")
t=t[t.account!="primary"].sort_values(["account","strategy","date","et"]).copy()
keep=np.ones(len(t),bool); pos={i:k for k,i in enumerate(t.index)}
for _,g in t.groupby(["account","strategy","date"]):
    et,xt,r=g.et.to_numpy(),g.xt.to_numpy(),g.r.to_numpy(); kept=[]
    for j in range(len(g)):
        if sum(r[k] for k in kept if xt[k]<=et[j])<=-2: keep[pos[g.index[j]]]=False
        else: kept.append(j)
t["keep"]=keep; rng=np.random.default_rng(11)
for f,g in t.groupby("fam"):
    act=-g[~g.keep].r.sum(); grp=[(gg.r.to_numpy(),(~gg.keep).sum()) for a,gg in g.groupby("account")]
    sims=np.array([sum(-r[rng.choice(len(r),k,replace=False)].sum() for r,k in grp if k) for _ in range(1000)])
    # worst day effect
    d0=g.groupby("date").r.sum(); d1=g[g.keep].groupby("date").r.sum().reindex(d0.index,fill_value=0)
    print(f"{f}: actual {act:.1f}; random same account any day mean {sims.mean():.1f} p5 {np.percentile(sims,5):.1f} p95 {np.percentile(sims,95):.1f} pct {(sims<act).mean()*100:.0f}; worst day {d0.min():.0f}->{d1.min():.0f}")
