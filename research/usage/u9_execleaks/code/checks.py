"""U9 descriptive checks + B1 quote pre-check effect (as run 2026-11-18; argv[1] = scratch dir with j/*.db, borrow/,
assets_now.json.gz). Q2 slot displacement, Q3 flag stability, B1 effect on filled trades (live R, signals.info quote)."""
import sqlite3, glob, json, gzip, sys
import numpy as np, pandas as pd
S = sys.argv[1]
def journals(q):
    out = []
    for f in sorted(glob.glob(f"{S}/j/*.db")):
        d = pd.read_sql(q, sqlite3.connect(f)); d["acct"] = f.split("/")[-1][:-3]; out.append(d)
    return pd.concat(out, ignore_index=True)
A = journals("select day,ts,symbol,strategy,side,status,reason from signals where status in ('submitted','skipped','rejected')")
A["poll"] = A.ts.str[:16]
e = A[A.reason == "not shortable/ETB"]; sub = A[A.status == "submitted"]
k = ["acct", "poll", "strategy"]
m = e[k].drop_duplicates().merge(sub[k].drop_duplicates().assign(s=1), on=k, how="left")
print("Q2 ETB-skip polls", len(m), "same setup submitted another name same poll", int(m.s.sum()))
print("Q2 rank-capped setups ETB skips", e.strategy.str.match(r"^(orb|orb20|vwap_pullback|vwap_reclaim)").sum())
# Q3
S_ = A[(A.side == -1)]
for day in ("2026-11-04", "2026-11-05"):
    b = pd.read_csv(f"{S}/borrow/{day}.csv.gz"); ok = dict(zip(b.symbol, (b.shortable == 1) & (b.easy_to_borrow == 1)))
    x = S_[S_.day == day]; sk = set(x[x.reason == "not shortable/ETB"].symbol); tr = set(x[x.status == "submitted"].symbol)
    print("Q3", day, "skipped", len(sk), "ETB@09:08", sum(ok.get(s, False) for s in sk), "traded", len(tr), "non-ETB@09:08", sum(not ok.get(s, False) for s in tr))
a = pd.DataFrame(json.load(gzip.open(f"{S}/assets_now.json.gz", "rt"))["assets"]); now = dict(zip(a.symbol, a.shortable & a.easy_to_borrow))
x = S_[S_.day == "2026-11-18"]; sk = set(x[x.reason == "not shortable/ETB"].symbol); tr = set(x[x.status == "submitted"].symbol)
print("Q3 11-18 skipped", len(sk), "ETB now", sum(now.get(s, False) for s in sk), "traded", len(tr), "non-ETB now", sum(not now.get(s, False) for s in tr))
# B1 effect on filled trades
s = journals("select day,strategy,side,stop,target,broker_order_id oid,info from signals where status='submitted' and day<='2026-11-17'")
t = journals("select broker_order_id oid,entry,stop st,shares,pnl_adj,pnl from trades where broker_order_id is not null")
t["R"] = t.pnl_adj.fillna(t.pnl) / ((t.entry - t.st).abs() * t.shares); t = t.groupby("oid").R.sum().reset_index()
q = s["info"].map(lambda i: json.loads(i) if i else {})
s["fill"] = [j.get("ask") if sd == 1 else j.get("bid") for j, sd in zip(q, s.side)]
s["exitq"] = [j.get("bid") if sd == 1 else j.get("ask") for j, sd in zip(q, s.side)]
s = s.dropna(subset=["fill"])
hitT = s[s.target.notna() & (s.side * (s.target - s.fill) <= 0.01)].merge(t, on="oid")
hitS = s[s.side * (s.exitq - s.stop) <= 0.01].merge(t, on="oid")
for nm, x in (("target", hitT), ("stop", hitS)):
    print("B1", nm, "n", len(x), "avgR", round(x.R.mean(), 4), "totR", round(x.R.sum(), 2))
    for h, g in x.groupby(np.where(x.day <= "2026-10-22", "fit", "check")):
        gain = -g.R; print("  ", h, len(g), round(gain.sum(), 2), "t", round(gain.mean() / (gain.std() / np.sqrt(len(g))), 2) if len(g) > 2 else None)
for nm, x in (("target", hitT), ("stop", hitS)):
    d = (-x.R).groupby(x.day).sum(); g = (-x.R).groupby(x.strategy).sum()
    print("B1", nm, "days", len(d), "best-day share of gain", round(d.max() / d.sum(), 3), "gain w/o best day", round(d.sum() - d.max(), 2),
          "| setups improve", int((g > 0).sum()), round(g[g > 0].sum(), 2), "worse", int((g < 0).sum()), round(g[g < 0].sum(), 2))
    x.groupby("strategy").R.agg(["size", "sum"]).to_csv(f"{S}/b1_{nm}_bysetup.csv")
