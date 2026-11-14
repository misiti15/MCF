"""SIZETREND - when the SIZE of a day is predictable at the open, is the day also more DIRECTIONAL (trend-like)? (descriptive, 0 configs)
A two-sided bracket (direction-free) gains in R units only if predicted-big days trend more cleanly, not just move more. Size and
costs scale together, so bigger alone does not pay. Names: SHORTUP's 489 top-adv stocks; daily + 30-min bars 2025-03..2026-11 (scratch).
Predicted size at 09:30 = |gap| / ATR% (gap = open / prior close - 1; ATR% 14-day, days < D) quintile within the day.
Outcomes after 10:00 (tradable part; uses the 10:00 bar open to the 15:30 bar close):
  size_after = (high - low after 10:00) / ATR%;  eff_after = |close - open_10:00| / (high - low after 10:00)  (1 = straight line);
  trend_share = P(eff_after >= 0.6).  Whole-day eff (open->close / day range) printed beside.
Null for eff: a random walk with the same bars gives eff ~0.35-0.45 regardless of scale, so compare quintiles with each other.
    python -I sizetrend.py <shortup data dir>        Educational only - not financial advice."""
import sys, numpy as np, pandas as pd
D = sys.argv[1]
d = pd.read_csv(f"{D}/daily.csv.gz"); d["date"] = d.t.str[:10]; d = d.sort_values(["symbol", "date"])
pc = d.groupby("symbol").c.shift(1); gp = (pd.to_datetime(d.date) - pd.to_datetime(d.groupby("symbol").date.shift(1))).dt.days
pc[gp > 5] = np.nan
d["tr"] = np.maximum(d.h, pc) - np.minimum(d.l, pc)
d["atrp"] = d.groupby("symbol").tr.transform(lambda x: x.rolling(14, min_periods=10).mean().shift(1)) / pc
d["gapA"] = (d.o / pc - 1).abs() / d.atrp
d["eff_day"] = (d.c - d.o).abs() / (d.h - d.l)
m = pd.read_csv(f"{D}/m30.csv.gz"); m["t"] = pd.to_datetime(m.t, utc=True).dt.tz_convert("America/New_York")
m["date"] = m.t.dt.strftime("%Y-%m-%d"); m["hm"] = m.t.dt.hour * 100 + m.t.dt.minute
a = m[(m.hm >= 1000) & (m.hm <= 1530)].sort_values("t")
g = a.groupby(["symbol", "date"]).agg(o10=("o", "first"), hi=("h", "max"), lo=("l", "min"), cl=("c", "last"), nb=("o", "size")).reset_index()
g = g[g.nb >= 11]
X = g.merge(d[["symbol", "date", "atrp", "gapA", "eff_day"]], on=["symbol", "date"]).dropna()
X = X[(X.atrp > 0) & (X.hi > X.lo) & (X.date >= "2025-04-01")]
X["size_after"] = (X.hi - X.lo) / X.o10 / X.atrp; X["eff"] = (X.cl - X.o10).abs() / (X.hi - X.lo)
X["q"] = X.groupby("date").gapA.transform(lambda s: pd.qcut(s.rank(method="first"), 5, labels=False)) + 1
print(f"name-days {len(X)} ({X.date.min()}..{X.date.max()}, {X.symbol.nunique()} names, {X.date.nunique()} days)")
T = X.groupby("q").agg(gapA=("gapA", "median"), size_after=("size_after", "mean"), eff_after=("eff", "mean"),
                       trend_share=("eff", lambda e: (e >= 0.6).mean()), eff_day=("eff_day", "mean"), n=("eff", "size"))
print(T.round(3).to_string())
# day-clustered t of eff difference Q5 - Q1
dd = X[X.q == 5].groupby("date").eff.mean() - X[X.q == 1].groupby("date").eff.mean(); dd = dd.dropna()
print(f"eff_after Q5 - Q1: {dd.mean():+.4f} (day-t {dd.mean() / (dd.std(ddof=1) / np.sqrt(len(dd))):+.2f}, {len(dd)} days)")
sz = X[X.q == 5].groupby("date").size_after.mean() / X[X.q == 1].groupby("date").size_after.mean()
print(f"size_after Q5 / Q1 ratio: median {sz.median():.2f}")
print("Educational only - not financial advice.")
