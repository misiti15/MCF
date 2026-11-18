"""Graveyard deep dive 2026-11-18: per-resident live record, trend, day-type fit, correlation, pot cost.
Live journals run_id 1, all ten accounts, R after costs = pnl_adj / (|entry-stop| x shares); identical signals across
accounts (setup|symbol|date|entry minute) counted once. Locked block 2024-11-01..2025-02-28 excluded (not in live data).
Educational only - not financial advice."""
import sys, re, sqlite3, yaml, numpy as np, pandas as pd
S = sys.argv[1]; WT = sys.argv[2]; OUT = sys.argv[3]
ACC = {"mcf-data": "Primary", "mcf-data-testing": "On Deck", "mcf-data-testing2": "Testing A",
       "mcf-data-explore1": "Testing B", "mcf-data-livelab": "Testing C", "mcf-data-testingd": "Testing D",
       "mcf-data-testinge": "Testing E", "mcf-data-testingf": "Testing F", "mcf-data-gen": "Gen",
       "mcf-data-graveyard": "Graveyard"}
out = []
for b, a in ACC.items():
    c = sqlite3.connect(f"{S}/j/{b}.db")
    t = pd.read_sql("select symbol,strategy,side,date,entry_time,entry,stop,shares,pnl_adj,r_multiple,exit_reason "
                    "from trades where run_id=1 and exit_time is not null", c)
    t["acct"] = a; out.append(t)
t = pd.concat(out, ignore_index=True)
t = t[~t.date.between("2024-11-01", "2025-02-28")]
risk = (t.entry - t.stop).abs() * t.shares.abs()
t["R"] = np.where(t.pnl_adj.notna() & (risk > 0), t.pnl_adj / risk, t.r_multiple)
t = t[t.R.notna()]
et = pd.to_datetime(t.entry_time, utc=True, format="ISO8601").dt.tz_convert("America/New_York")
t["k"] = t.strategy + "|" + t.symbol + "|" + t.date + "|" + et.dt.strftime("%H%M")

raw = open(f"{WT}/config/account_graveyard.yaml").read(); y = yaml.safe_load(raw)
guests = set(re.findall(r"- (\S+)\s+# GY-BENCH guest", raw))
res = [k for k in y["strategies"] if k not in guests]
names = yaml.safe_load(open(f"{WT}/config/setup_names.yaml"))
dt = pd.read_csv(f"{WT}/research/usage/u5_daytype/u5_check_days.csv").set_index("date").dtype.to_dict()

prim = t[t.acct == "Primary"]
ptot = prim.groupby("strategy").R.sum()
winners = ptot[ptot > 0].index
pw_daily = prim[prim.strategy.isin(winners)].groupby("date").R.sum()
pdates = sorted(prim.date.unique())
pw_daily = pw_daily.reindex(pdates, fill_value=0.0)
p_all = prim.groupby("date").R.sum().reindex(pdates, fill_value=0.0)
gyd = t[(t.acct == "Graveyard")]
all_gy_dates = sorted(gyd.date.unique())

dd = t.sort_values("acct").drop_duplicates("k")
rows = []
for s in res:
    blk = y["strategies"][s]
    g = dd[dd.strategy == s]
    nm = names.get(s, {}).get("name", "") if isinstance(names.get(s), dict) else ""
    r = dict(setup=s, name=nm, side=("short" if "short" in s or blk.get("sides") == ["short"] else "long"),
             status=("off (moved to arena 11-13)" if blk.get("enabled") is False else
                     "benched 11-18..11-24" if blk.get("benched") else "active"),
             former_primary=bool(blk.get("former_primary")))
    if g.empty:
        rows.append(r); continue
    d = g.groupby("date").R.sum(); tot = d.sum(); bd = d.idxmax()
    gg = g[g.acct == "Graveyard"]; gdd = gg.groupby("date").R.sum()
    r.update(n=len(g), sessions=d.size, totR=tot, avgR=g.R.mean(), avg_wo_best=g[g.date != bd].R.mean(),
             best_day=bd, best_share=(d.max() / tot if tot > 0 else np.nan), green_pct=(d > 0).mean(),
             first=g.date.min(), last=g.date.max(), accts=";".join(sorted(g.acct.unique())),
             gy_n=len(gg), gy_sessions=gdd.size, gy_totR=gg.R.sum(), gy_avg=gg.R.mean() if len(gg) else np.nan,
             gy_wo_best=(gg[gg.date != gdd.idxmax()].R.mean() if gdd.size > 1 else np.nan),
             gy_trades_per_session=(len(gg) / gdd.size if gdd.size else np.nan))
    ds = d.sort_index()
    for k in (5, 10):
        last = ds.index[-k:]; gl = g[g.date.isin(last)]
        r[f"last{k}_n"] = len(gl); r[f"last{k}_avg"] = gl.R.mean(); r[f"last{k}_totR"] = gl.R.sum()
    g2 = g.assign(dtype=g.date.map(dt))
    for ty in ("up", "down", "quiet"):
        x = g2[g2.dtype == ty]; r[f"{ty}_n"] = len(x); r[f"{ty}_avg"] = x.R.mean() if len(x) else np.nan
    common = [x for x in pdates if x in set(d.index)]
    dz = d.reindex(pdates).dropna()
    if len(dz) >= 8:
        r["rho_primary_winners"] = np.corrcoef(dz.values, pw_daily.reindex(dz.index).values)[0, 1]
        r["rho_primary_all"] = np.corrcoef(dz.values, p_all.reindex(dz.index).values)[0, 1]
    # symbol overlap with Primary winners (same symbol, same date, same side)
    pk = set(prim[prim.strategy.isin(winners)].pipe(lambda x: x.symbol + "|" + x.date + "|" + x.side.astype(str)))
    r["overlap_primary_winner_pct"] = (g.symbol + "|" + g.date + "|" + g.side.astype(str)).isin(pk).mean()
    rows.append(r)
R = pd.DataFrame(rows)
R.to_csv(f"{OUT}/raw_stats.csv", index=False)

# pot cost: Graveyard account per session (residents vs guests)
gya = t[t.acct == "Graveyard"].copy()
gya["grp"] = np.where(gya.strategy.isin(guests), "guest", "resident")
ps = gya.groupby(["date", "grp"]).R.agg(["size", "sum"]).unstack(fill_value=0)
ps.to_csv(f"{OUT}/pot_per_session.csv")
c = sqlite3.connect(f"{S}/j/mcf-data-graveyard.db")
sig = pd.read_sql("select day as date, count(*) n from signals where run_id=1 group by day", c).set_index("date").n
od = pd.read_sql("select substr(created_at,1,10) date, count(*) n from orders group by 1", c) if \
    "created_at" in [x[1] for x in c.execute("pragma table_info(orders)")] else None
pd.set_option("display.width", 250); pd.set_option("display.max_rows", 200); pd.set_option("display.max_columns", 60)
print(R[["setup", "status", "n", "sessions", "avgR", "avg_wo_best", "best_share", "totR", "gy_n", "gy_avg", "gy_wo_best",
         "last5_avg", "last10_avg", "up_avg", "down_avg", "quiet_avg", "rho_primary_winners", "overlap_primary_winner_pct"]]
      .round(3).to_string(index=False))
print("primary winners:", list(winners))
print(ps.tail(12)); print("sessions", ps.shape[0])
print("resident per-session mean trades/R (last 10):", ps.tail(10).mean().round(2).to_dict())
print("signals/session last 5:", sig.tail(5).to_dict())
if od is not None: print("orders/session last 5:", od.tail(5).to_dict())
print("total resident R", gya[gya.grp == "resident"].R.sum().round(1), "n", (gya.grp == "resident").sum())
