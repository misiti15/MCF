"""Reviewer: basket cap and gap-up-shorts-off restricted to the Primary roster that trades from 11-30
(L3-fromopen, NM-ETF, RW3, RW5; MF2/MF4 left Primary 11-20, ST7 11-23). Usage: python roster.py <journal.db> <days_primary.csv>.
Educational only - not financial advice."""
import sqlite3, sys, numpy as np, pandas as pd
from mcf.config import load_config
from mcf.costs import cost_r_lr8
ROSTER = ["L3-gap-slope-fromopen-FD", "NM-ETF-late-dip-di-long", "RW3-gapdn-rsi5pop-flowsell-short-FD", "RW5-heat30-flowsell-rsi5pop-gapdn-short-FD"]
con = sqlite3.connect(sys.argv[1]); x = pd.read_sql("SELECT * FROM trades WHERE run_id=1 AND exit_time IS NOT NULL", con); con.close()
x["date"] = x.date.astype(str).str[:10]; x = x[x.date >= "2026-10-23"].copy()
x["r"] = cost_r_lr8(x, load_config()).astype(float); x = x[x.r.notna()]
x["et"] = pd.to_datetime(x.entry_time, utc=True, format="mixed")
x = x.sort_values(["date", "strategy", "et"]); x["k"] = x.groupby(["date", "strategy"]).cumcount() + 1
days = sorted(x.date.unique()); x = x[x.strategy.isin(ROSTER)].copy()
gap = pd.read_csv(sys.argv[2]).set_index("date").spy_gap
d = x.groupby("date").r.sum().reindex(days, fill_value=0.0)
def t(v): v = np.asarray(v); return v.mean() / (v.std(ddof=1) / np.sqrt(len(v)))
rng = np.random.default_rng(9)
print(f"roster lots {len(x)} R {x.r.sum():+.1f} avg {x.r.mean():+.3f}; by setup", x.groupby("strategy").r.sum().round(1).to_dict())
def ev(name, w):
    nd = (x.r * w).groupby(x.date).sum().reindex(days, fill_value=0.0); dd = nd - d
    ex = int(round((1 - w).sum())); u = []
    for _ in range(1000):
        m = np.ones(len(x)); m[rng.choice(len(x), ex, replace=False)] = 0; u.append((x.r * m).sum() - x.r.sum())
    u = np.array(u)
    print(f"{name}: cut {100*(1-w).sum()/len(x):.0f}% saved {dd.sum():+.1f} ({dd.sum()/5:+.1f}/wk) U {u.mean():+.1f} excess {(dd.sum()-u.mean())/5:+.1f}/wk pct {100*(u<dd.sum()).mean():.0f} dt {t(dd):.2f} "
          f"ex-best {dd.sum()-dd.max():+.1f} best-share {dd.max()/dd.sum() if dd.sum()>0 else float('nan'):.2f} green-cost {dd[d>0].sum():+.1f} red {int((d<=0).sum())}->{int((nd<=0).sum())}")
ev("K5 skip", np.where(x.k <= 5, 1.0, 0.0)); ev("K5 half", np.where(x.k <= 5, 1.0, 0.5))
sh = (x.side < 0).values & (x.date.map(gap) > 0.3).values
ev("no shorts gap-up>0.3", np.where(sh, 0.0, 1.0))
