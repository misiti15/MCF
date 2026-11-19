"""GY-ARCHIVE-20 exemption check (owner 2026-11-18: "unless any graveyard setups have high volume trades daily with
potential huge gain clusters per day in which case our market compass can help switch that on/off in the future").

Thresholds fixed BEFORE the numbers were computed (0 tuned configs; one pass):
  HIGH volume  : whole live record (identical signals across accounts counted once) averages >= 15 trades per active
                 session.
  BIG-DAY cluster: >= 3 sessions with a day total >= +10R (R after costs, journal pnl_adj basis) AND those sessions
                 together >= +40R.
A setup meeting BOTH is EXEMPT from GY-ARCHIVE-20 (it stays a Graveyard resident, KEEP-TESTING, and is listed as a
Market Compass on/off candidate). Day-type split of the big days (hindsight SPY open-to-close, u5 labels) is reported,
not gated. Live journals run_id 1; locked block not in live data. Educational only - not financial advice.
Usage: python gy_exempt.py <journal_dir> <worktree>"""
import sys, sqlite3, numpy as np, pandas as pd

J, WT = sys.argv[1], sys.argv[2]
ACC = ["mcf-data", "mcf-data-testing", "mcf-data-testing2", "mcf-data-explore1", "mcf-data-livelab",
       "mcf-data-testingd", "mcf-data-testinge", "mcf-data-testingf", "mcf-data-gen", "mcf-data-graveyard"]
names = open(f"{WT}/research/graveyard_review_1118/code/archive_list.txt").read().split()
out = []
for b in ACC:
    c = sqlite3.connect(f"{J}/{b}.db")
    t = pd.read_sql("select symbol,strategy,date,entry_time,entry,stop,shares,pnl_adj,r_multiple from trades "
                    "where run_id=1 and exit_time is not null", c)
    t["acct"] = b
    out.append(t[t.strategy.isin(names)])
t = pd.concat(out, ignore_index=True)
risk = (t.entry - t.stop).abs() * t.shares.abs()
t["R"] = np.where(t.pnl_adj.notna() & (risk > 0), t.pnl_adj / risk, t.r_multiple)
t = t[t.R.notna()]
et = pd.to_datetime(t.entry_time, utc=True, format="ISO8601").dt.tz_convert("America/New_York")
t["k"] = t.strategy + "|" + t.symbol + "|" + t.date + "|" + et.dt.strftime("%H%M")
t = t.sort_values("acct").drop_duplicates("k")
try:
    dt = pd.read_csv(f"{WT}/research/usage/u5_daytype/u5_check_days.csv").set_index("date").dtype.to_dict()
except Exception:
    dt = {}
rows = []
for s in names:
    g = t[t.strategy == s]
    d = g.groupby("date").R.agg(["sum", "size"])
    big = d[d["sum"] >= 10]
    tps = len(g) / max(len(d), 1)
    vol = tps >= 15
    clus = len(big) >= 3 and big["sum"].sum() >= 40
    types = pd.Series([dt.get(x, "?") for x in big.index]).value_counts().to_dict() if len(big) else {}
    rows.append(dict(setup=s, trades=len(g), sessions=len(d), trades_per_session=round(tps, 1),
                     total_R=round(g.R.sum(), 1), best_day_R=round(d["sum"].max(), 1) if len(d) else np.nan,
                     days_ge_10R=len(big), big_days_R=round(big["sum"].sum(), 1), big_day_types=types,
                     high_volume=vol, big_day_cluster=clus, exempt=vol and clus))
r = pd.DataFrame(rows).sort_values(["exempt", "trades_per_session"], ascending=False)
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 20)
print(r.to_string(index=False))
print("exempt:", list(r[r.exempt].setup))
