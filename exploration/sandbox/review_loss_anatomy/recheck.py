"""Reviewer re-check of loss_anatomy headline numbers on Primary (independent code path).
Usage: python recheck.py <journal.db>. Educational only - not financial advice."""
import sqlite3, sys, numpy as np, pandas as pd
from mcf.config import load_config
from mcf.costs import cost_r_lr8
con = sqlite3.connect(sys.argv[1])
x = pd.read_sql("SELECT * FROM trades WHERE run_id=1 AND exit_time IS NOT NULL", con); con.close()
x["date"] = x.date.astype(str).str[:10]; x = x[x.date >= "2026-10-23"].copy()
x["r"] = cost_r_lr8(x, load_config()).astype(float); x = x[x.r.notna()]
x["et"] = pd.to_datetime(x.entry_time, utc=True, format="mixed")
x = x.sort_values(["date", "strategy", "et"]); x["k"] = x.groupby(["date", "strategy"]).cumcount() + 1
d = x.groupby("date").r.sum(); neg = d[d < 0]
print(f"lots {len(x)} total R {x.r.sum():.1f} days {len(d)} red {int((d<=0).sum())} losing-day R {neg.sum():.1f} worst5 {d.nsmallest(5).sum():.1f} share {d.nsmallest(5).sum()/neg.sum():.2f}")
print("worst5:", d.nsmallest(5).round(1).to_dict())
rng = np.random.default_rng(123)
def t(v): v = np.asarray(v); return v.mean() / (v.std(ddof=1) / np.sqrt(len(v)))
for K in [5]:
    for w6 in [0.0, 0.5]:
        w = np.where(x.k <= K, 1.0, w6); nd = (x.r * w).groupby(x.date).sum(); dd = nd - d
        ex = int(round((1 - w).sum())); u = []; uex = []
        for _ in range(1000):
            m = np.ones(len(x)); m[rng.choice(len(x), ex, replace=False)] = 0
            un = (x.r * m).groupby(x.date).sum(); u.append(un.sum() - d.sum())
        u = np.array(u)
        print(f"K{K} w6={w6}: cut {100*(1-w).sum()/len(x):.0f}% saved {dd.sum():+.1f} ({dd.sum()/5:+.1f}/wk) U mean {u.mean():+.1f} excess {dd.sum()-u.mean():+.1f} ({(dd.sum()-u.mean())/5:+.1f}/wk) pct {100*(u<dd.sum()).mean():.1f} dt {t(dd):.2f} "
              f"best-day share {dd.max()/dd.sum():.2f} ex-best {dd.sum()-dd.max():+.1f} green-cost {dd[d>0].sum():+.1f} worst5 {nd.nsmallest(5).sum():.1f} red {int((nd<=0).sum())}")
        # excess over expected proportional cut, per day (day-clustered): dd - frac*base
        frac = (1 - w).sum() / len(x); exd = dd + frac * d
        print(f"   day-clustered t of excess over a proportional size cut: {t(exd):.2f} (excess {exd.sum():+.1f})")
        st = (x.r * w - x.r).groupby(x.strategy).sum(); pos = x[x.r>0].groupby("strategy").r.sum()
        print("   per setup delta:", st[st!=0].round(1).sort_values().to_dict())
# L3 11-25
p = x[(x.date == "2026-11-25") & x.strategy.str.startswith("L3")]
print("11-25 L3 lots", len(p), "stops", int((p.exit_reason == "stop").sum()), "R", round(p.r.sum(), 1))
