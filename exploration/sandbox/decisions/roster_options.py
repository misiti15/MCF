"""Decision support (descriptive, live, in-sample): Primary's 11-30 roster (L3-fromopen, NM-ETF, RW3, RW5) on its own
live Primary lots since 10-23 (LR8 R after costs, run 1), under lineup options. A removal on live lots is a pure
exposure cut (no replay of freed slots). Usage: python roster_options.py <primary journal.db>
Educational only - not financial advice."""
import sqlite3, sys, numpy as np, pandas as pd
from mcf.config import load_config
from mcf.costs import cost_r_lr8
L3, NM = "L3-gap-slope-fromopen-FD", "NM-ETF-late-dip-di-long"
RW3, RW5 = "RW3-gapdn-rsi5pop-flowsell-short-FD", "RW5-heat30-flowsell-rsi5pop-gapdn-short-FD"
ROSTER = [L3, NM, RW3, RW5]
con = sqlite3.connect(sys.argv[1]); x = pd.read_sql("SELECT * FROM trades WHERE run_id=1 AND exit_time IS NOT NULL", con); con.close()
x["date"] = x.date.astype(str).str[:10]; x = x[x.date >= "2026-10-23"].copy()
x["r"] = cost_r_lr8(x, load_config()).astype(float); x = x[x.r.notna()]
days = sorted(x.date.unique()); x = x[x.strategy.isin(ROSTER)].copy()
print(f"sessions {len(days)}; roster lots {len(x)}; R {x.r.sum():+.1f}")
print(x.groupby("strategy").agg(lots=("r", "size"), R=("r", "sum"), avg=("r", "mean"), days=("date", "nunique")).round(3))
wk = pd.Series(pd.to_datetime(days)).dt.to_period("W-FRI").astype(str).values
def t(v): v = np.asarray(v); return v.mean() / (v.std(ddof=1) / np.sqrt(len(v)))
def show(name, keep):
    y = x[x.strategy.isin(keep)]
    d = y.groupby("date").r.sum().reindex(days, fill_value=0.0)
    w = d.groupby(wk).sum()
    best = d.max()
    print(f"{name:28s} lots {len(y):4d} R {d.sum():+7.1f} R/day {d.mean():+5.2f} day-t {t(d):+5.2f} sd {d.std():5.1f} "
          f"red {int((d < 0).sum()):2d}/{len(d)} worst {d.min():+6.1f} worst5 {d.nsmallest(5).sum():+7.1f} "
          f"w/o best {d.sum()-best:+7.1f} weeks {' '.join(f'{v:+.1f}' for v in w.values)} green wks {int((w > 0).sum())}/{len(w)}")
show("as-is (4 setups)", ROSTER)
show("L3 out", [NM, RW3, RW5])
show("L3 + RW5 out", [NM, RW3])
show("all shorts out (NM only)", [NM])
# L3 per day: big days
l3 = x[x.strategy == L3].groupby("date").agg(lots=("r", "size"), R=("r", "sum")).sort_values("R")
print("L3 worst/best days:\n", pd.concat([l3.head(4), l3.tail(4)]).round(1))
print("Educational only - not financial advice.")
