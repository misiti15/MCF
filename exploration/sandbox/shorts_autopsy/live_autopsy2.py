"""shorts_autopsy live part 2: how much of the short loss is one day (11-25), market beta, and the gap-down family.
Reads live_feat.parquet from live_autopsy.py. Usage: python live_autopsy2.py SCRATCH. Educational only - not financial advice."""
import sys
import numpy as np, pandas as pd
D = sys.argv[1]
t = pd.read_parquet(f"{D}/live_feat.parquet")
def st(g):
    ds = g.groupby("date").r.sum(); se = ds.std(ddof=1) / np.sqrt(len(ds))
    return pd.Series(dict(n=len(g), sess=len(ds), avgR=g.r.mean(), gross=g.r_gross.mean(), R=g.r.sum(), day_t=ds.mean() / se,
                          green=(ds > 0).sum(), worst=ds.min(), wo_worst=(g.r.sum() - ds.min()) / len(g), wo_best=(g.r.sum() - ds.max()) / len(g)))
print("## Side / family, with and without 11-25")
for lab, x in (("all", t), ("ex 11-25", t[t.date != "2026-11-25"])):
    print(lab); print(x.groupby("fam").apply(st).round(3).to_string())
print("\n## Beta decomposition (r_gross on SPY % move during hold), per family; market-neutral gross = intercept")
for lab, x in (("all", t), ("ex 11-25", t[t.date != "2026-11-25"])):
    for f, g in x[x.spy_hold.notna()].groupby("fam"):
        b = np.polyfit(g.spy_hold, g.r_gross, 1)
        # per-trade beta in R per 1% SPY; mean move; alpha and its day-clustered t
        res = g.r_gross - b[0] * g.spy_hold
        ds = res.groupby(g.date).mean(); tt = ds.mean() / (ds.std(ddof=1) / np.sqrt(len(ds)))
        print(f"{lab:9s} {f:20s} n {len(g):5d} slope {b[0]:+.3f} R/1%SPY  intercept {b[1]:+.3f}  mean SPYhold {g.spy_hold.mean():+.3f}%"
              f"  beta-neutral gross {res.mean():+.3f} (day t {tt:+.2f})  cost {g.cost_r.mean():.3f}")
print("\n## Shorts by SPY gap x family (ex 11-25 shown separately)")
t["spygap_b"] = pd.cut(t.spy_gap, [-10, -0.5, 0.5, 10], labels=["SPY gap<=-0.5", "flat", "SPY gap>=+0.5"])
for lab, x in (("all", t), ("ex 11-25", t[t.date != "2026-11-25"])):
    print(lab); print(x[x.side < 0].groupby(["fam", "spygap_b"], observed=True).apply(st).round(3).to_string())
print("\n## Shorts by stock gap x family, ex 11-25")
x = t[(t.side < 0) & (t.date != "2026-11-25")]
print(x.assign(b=pd.cut(x.gap, [-100, -5, -2.66, -1, 1, 100])).groupby(["fam", "b"], observed=True).apply(st).round(3).to_string())
print("\n## Shorts by entry hour, ex 11-25")
print(x.assign(b=pd.cut(x.tod, [900, 1030, 1200, 1400, 1600])).groupby(["fam", "b"], observed=True).apply(st).round(3).to_string())
print("\n## Day-level: short-book R vs SPY open->close (sessions)")
dd = t[t.side < 0].groupby("date").agg(R=("r", "sum"), n=("r", "size"), oc=("oc_m", "first"), gap=("spy_gap", "first"), pm=("pm", "first"))
print("corr(short R/day, SPY oc) %.2f; corr with SPY PM leg %.2f" % (dd.R.corr(dd.oc), dd.R.corr(dd.pm)))
print(dd.sort_values("R").head(6).round(2).to_string())
print("\n## 11-25 anatomy (shorts): by family and entry hour")
y = t[(t.date == "2026-11-25") & (t.side < 0)]
print(y.groupby("fam").apply(lambda g: pd.Series(dict(n=len(g), R=g.r.sum(), avg=g.r.mean(), stop_share=(g.exit_reason == "stop").mean()))).round(3).to_string())
print(y.assign(b=pd.cut(y.tod, [900, 1000, 1030, 1100, 1200, 1300, 1400, 1600])).groupby("b", observed=True).r.agg(["size", "sum", "mean"]).round(2).to_string())
print("top setups 11-25:", y.groupby("strategy").r.sum().sort_values().head(8).round(1).to_dict())
print("accounts 11-25:", y.groupby("account").r.sum().round(1).to_dict())
