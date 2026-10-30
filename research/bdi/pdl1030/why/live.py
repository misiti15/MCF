"""pdl1030/why live anatomy: paper journals (run_id 1), R after costs = pnl_adj / $ risk. Educational only - not financial advice."""
import sqlite3, numpy as np, pandas as pd
J = "/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/j1030"
rows = []
for a in ("p", "t1", "t2", "gy", "gen"):
    c = sqlite3.connect(f"file:{J}/{a}/journal.db?mode=ro", uri=True)
    t = pd.read_sql("select * from trades where run_id=1 and exit is not null and strategy like 'CWT14-failbrk-pdl-%'", c)
    t["acct"] = a; rows.append(t)
T = pd.concat(rows, ignore_index=True)
T["pnl_adj"] = T.pnl_adj.fillna(T.pnl); T["stop"] = T.stop.astype(float); T["risk"] = (T.entry - T.stop).abs() * T.shares
T["rc"] = np.where(T.risk > 0, T.pnl_adj / T.risk, T.r_multiple)
T["et"] = pd.to_datetime(T.entry_time, utc=True, format="mixed").dt.tz_convert("America/New_York")
T["hm"] = T.et.dt.hour * 100 + T.et.dt.minute
T["tgtR"] = (T.target.astype(float) - T.entry) / (T.entry - T.stop)
T["hold"] = (pd.to_datetime(T.exit_time, utc=True, format="mixed") - pd.to_datetime(T.entry_time, utc=True, format="mixed")).dt.total_seconds() / 60
T["st"] = T.strategy.str.replace("CWT14-failbrk-pdl-", "")
def agg(g):
    return pd.Series({"n": len(g), "avgR": g.rc.mean(), "win": (g.rc > 0).mean(), "sumR": g.rc.sum()})
out = []
P = lambda s, d: out.append(f"\n## {s}\n" + d.round(3).to_string())
P("by setup", T.groupby("st").apply(agg))
P("exit reason (all)", T.groupby("exit_reason").apply(agg).join(T.groupby("exit_reason").hold.median().rename("med_hold_min")))
T["tb"] = pd.cut(T.hm, [929, 1000, 1030, 1100, 1200, 1300, 1400, 1501], labels=["9:50-10", "10-10:30", "10:30-11", "11-12", "12-13", "13-14", "14-15"])
P("by entry time", T.groupby("tb", observed=True).apply(agg))
P("target distance in R (entry->target / entry->stop)", T.tgtR.describe(percentiles=[.1, .25, .5, .75, .9]).to_frame())
T["post"] = np.where(T.date >= "2026-10-27", "since 10-27", "before 10-27")
P("target R by period", T.groupby("post").tgtR.describe(percentiles=[.5]))
P("by period", T.groupby("post").apply(agg))
day = T.groupby("date").agg(n=("rc", "size"), R=("rc", "sum"), avg=("rc", "mean"), win=("rc", lambda v: (v > 0).mean()))
P("per session (all PDL longs merged)", day)
w = T[T.rc > 0]; lz = T[T.rc <= 0]
out.append(f"\nwinners avg {w.rc.mean():+.3f}R (median hold {w.hold.median():.0f} min); losers avg {lz.rc.mean():+.3f}R (median hold {lz.hold.median():.0f} min)")
s = T[T.exit_reason == "stop"]
out.append(f"stops: {len(s)} ({len(s)/len(T):.1%}) avg {s.rc.mean():+.3f}R; median minutes to stop {s.hold.median():.0f}; within 30 min {(s.hold<=30).mean():.1%}")
txt = "\n".join(out); print(txt); open(__file__.replace("live.py", "live_out.txt"), "w").write(txt + "\n\nEducational only - not financial advice.\n")
s2 = T[T.exit_reason == "stop"]
o2 = [f"stop exit slippage: median R on stops {s2.rc.median():+.3f}, p10 {s2.rc.quantile(.1):+.3f}",
      "target R quantiles: " + T.tgtR.astype(float).quantile([.1, .25, .5, .75, .9]).round(3).to_dict().__repr__(),
      "by period target R median: " + T.groupby("post").tgtR.median().round(3).to_dict().__repr__()]
for k, g in T.groupby("st"):
    o2.append(f"{k}: by entry bucket " + "; ".join(f"{b} {len(x)}/{x.rc.mean():+.3f}" for b, x in g.groupby("tb", observed=True)))
print("\n".join(o2)); open(__file__.replace("live.py", "live_out.txt"), "a").write("\n".join(o2) + "\n")
