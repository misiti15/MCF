import sys, re, yaml, numpy as np, pandas as pd
sys.path.insert(0, '.')
from jload import load, S
y = yaml.safe_load(open(S + "/gy.yaml"))
raw = open(S + "/gy.yaml").read()
guests = set(re.findall(r"- (\S+)\s+# GY-BENCH guest", raw))
res = [k for k in y["strategies"] if k not in guests]
t = load()
t["et"] = pd.to_datetime(t.entry_time, utc=True, format="ISO8601").dt.tz_convert("America/New_York")
t["hhmm"] = t.et.dt.hour * 100 + t.et.dt.minute
t = t[t.strategy.isin(res)].copy()
# dedup identical signals across accounts (same setup, symbol, date, entry minute)
t["k"] = t.strategy + "|" + t.symbol + "|" + t.date + "|" + t.et.dt.strftime("%H%M")
t = t.sort_values("acct").drop_duplicates("k")
t.to_pickle(S + "/gy_trades.pkl")
rows = []
for s, g in t.groupby("strategy"):
    d = g.groupby("date").R.sum()
    bd = d.idxmax(); tot = d.sum()
    gyg = g[g.acct == "Graveyard"]
    rows.append(dict(setup=s, n=len(g), days=d.size, totR=tot, avg=g.R.mean(),
                     avg_wo_best=g[g.date != bd].R.mean(), best_share=(d.max() / tot if tot > 0 else np.nan),
                     n_gy=len(gyg), avg_gy=gyg.R.mean(), first=g.date.min(), accts=",".join(sorted(g.acct.unique())),
                     enabled=y["strategies"][s].get("enabled", True), benched=bool(y["strategies"][s].get("benched"))))
r = pd.DataFrame(rows).sort_values("avg_wo_best", ascending=False)
missing = [s for s in res if s not in set(r.setup)]
pd.set_option("display.width", 250); pd.set_option("display.max_rows", 100)
print(r.round(3).to_string(index=False)); print("no live trades:", missing); print(len(res))
r.to_csv(S + "/roster.csv", index=False)
