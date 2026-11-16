import pandas as pd, numpy as np, json, sys
"""Live component analysis of MF2-FD (journal trades, run from the scratch dir). Educational only - not financial advice."""
t = pd.read_parquet("live_trades.parquet")
et = pd.to_datetime(t.entry_time, utc=True, format="mixed").dt.tz_convert("America/New_York")
xt = pd.to_datetime(t.exit_time, utc=True, format="mixed").dt.tz_convert("America/New_York")
t["em"] = et.dt.hour * 60 + et.dt.minute; t["hold"] = (xt - et).dt.total_seconds() / 60
t["risk"] = (t.entry - t.stop).abs()
t["costr"] = (2 * (0.01 + 1e-4 * t.entry) + 0.02) / t.risk
t["refire"] = t.meta.fillna("").str.contains('"refire": true')
s = pd.read_parquet("spy1m.parquet"); s.index = s.index.tz_convert("America/New_York")
s = s.assign(date=s.index.strftime("%Y-%m-%d"), mn=s.index.hour * 60 + s.index.minute)
oc = s.groupby("date").apply(lambda g: g.close.iloc[-1] / g.open.iloc[0] * 100 - 100)
ref = s[s.mn == 589].set_index("date").close
def spy_at(r):
    g = s[(s.date == r.date) & (s.mn <= r.em - 1)]
    return (g.close.iloc[-1] / ref.get(r.date, np.nan) - 1) * 100 if len(g) and r.date in ref else np.nan
t["spy950"] = t.apply(spy_at, axis=1)
t["spyday"] = t.date.map(oc)
t["dtype"] = np.where(t.spyday > 0.25, "up", np.where(t.spyday < -0.25, "down", "flat"))
t.loc[t.spyday.isna(), "dtype"] = "n/a"
def g(x): return f"n{len(x):4d} avg {x.r.mean():+.3f} tot {x.r.sum():+6.1f} win {(x.r>0).mean():.0%}"
print("ALL", g(t))
for col, bins in (("em", [0, 600, 630, 690, 780, 900, 1000]), ("spy950", [-9, -0.5, -0.2, 0, 0.2, 0.4, 9]), ("costr", [0, 0.08, 0.12, 0.15, 0.25, 9]),
                  ("entry", [0, 20, 50, 100, 300, 1e5]), ("hold", [0, 10, 30, 60, 120, 400])):
    print("--", col)
    for k, x in t.groupby(pd.cut(t[col], bins), observed=True): print(f"  {str(k):18s}", g(x))
for col in ("dtype", "exit_reason", "refire", "acct"):
    print("--", col)
    for k, x in t.groupby(col): print(f"  {str(k):18s}", g(x))
print("-- by day"); d = t.groupby("date").agg(n=("r", "size"), R=("r", "sum"), spy=("spyday", "first")); print(d.round(2).to_string())
print("stop share", (t.exit_reason == "stop").mean(), "mfe of stopped >=1:", ((t.exit_reason=="stop") & (t.mfe_r >= 1)).sum(), ">=0.5", ((t.exit_reason=="stop") & (t.mfe_r >= 0.5)).sum())
print("flatten trades mfe", t[t.exit_reason=="flatten"][["r","mfe_r","mae_r"]].describe().round(2))
print(t.sort_values("r")[["acct","symbol","date","em","entry","risk","costr","spy950","exit_reason","r","mfe_r","mae_r","hold","refire"]].head(5).round(3).to_string())
print(t.sort_values("r")[["acct","symbol","date","em","entry","risk","costr","spy950","exit_reason","r","mfe_r","mae_r","hold","refire"]].tail(5).round(3).to_string())
t.to_parquet("live_an.parquet")
