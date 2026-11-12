"""FILLCOST - what entry latency costs in R, per account (descriptive, 0 configs; Observer obs-fillclock side fact).
Live paper trades 10-20..11-11 (7 journals, pnl_adj not null). From trades.meta: bar_age_min (decision bar close -> order),
spread_bps; slip_bps (fill vs reference). slip_R = slip_bps/1e4 x entry / |entry - stop| (cost in R of the entry slip).
Regression per trade: slip_R ~ bar_age_min + spread_R (spread in R) + account dummies; and within-account slopes.
    python -I fillcost.py <journal dir>        Educational only - not financial advice."""
import sys, glob, os, json, sqlite3, numpy as np, pandas as pd
NAME = {"mcf-data": "Primary", "mcf-data-testing": "On Deck", "mcf-data-testing2": "Testing A", "mcf-data-explore1": "Testing B",
        "mcf-data-livelab": "Testing C", "mcf-data-gen": "Gen", "mcf-data-graveyard": "Graveyard"}
R = []
for p in sorted(glob.glob(f"{sys.argv[1]}/mcf-data*.db")):
    b = os.path.basename(p)[:-3]
    if b not in NAME: continue
    c = sqlite3.connect(p); pid = ",".join(str(r[0]) for r in c.execute("select id from runs where kind='paper'"))
    t = pd.read_sql(f"select date, strategy, side, signal_time, entry_time, entry, stop, shares, slip_bps, pnl_adj, meta from trades "
                    f"where run_id in ({pid}) and pnl_adj is not null and date >= '2026-10-20' and date <= '2026-11-11'", c)
    t["account"] = NAME[b]; R.append(t)
T = pd.concat(R, ignore_index=True)
def mget(s, k):
    try: return float(json.loads(str(s).split("};")[0].rstrip("}") + "}").get(k))   # meta may carry ';touch_fill' etc. after the JSON
    except Exception: return np.nan
T["bar_age"] = T.meta.map(lambda s: mget(s, "bar_age_min")); T["spread_bps"] = T.meta.map(lambda s: mget(s, "spread_bps"))
T["fill_s"] = (pd.to_datetime(T.entry_time, utc=True, format="mixed") - pd.to_datetime(T.signal_time, utc=True, format="mixed")).dt.total_seconds()
T["risk_pct"] = (T.entry - T.stop).abs() / T.entry
T = T[T.risk_pct > 0]
T["slip_R"] = T.slip_bps / 1e4 / T.risk_pct; T["spread_R"] = T.spread_bps / 1e4 / T.risk_pct
T["netR"] = T.pnl_adj / ((T.entry - T.stop).abs() * T.shares)
ok = T.dropna(subset=["bar_age", "slip_R", "spread_R"]); ok = ok[(ok.slip_R.abs() < 2) & (ok.bar_age >= 0) & (ok.bar_age < 10)]
print(f"net R all trades {T.netR.mean():+.3f}, kept {ok.netR.mean():+.3f} (selection check)")
print(f"trades {len(T)}; with bar_age / slip / spread in meta: {len(ok)} ({len(ok)/len(T):.0%}); window 10-20..11-11")
g = ok.groupby("account")
S = pd.DataFrame({"n": g.size(), "bar_age_med_min": g.bar_age.median(), "order_to_fill_med_s": g.fill_s.median(),
                  "spread_med_bps": g.spread_bps.median(), "slip_mean_bps": g.slip_bps.mean(), "slip_mean_R": g.slip_R.mean(),
                  "spread_mean_R": g.spread_R.mean(), "net_avg_R": g.netR.mean()})
pd.set_option("display.width", 220); print(S.round(3).to_string())
X = pd.get_dummies(ok.account, drop_first=True, dtype=float); X.insert(0, "spread_R", ok.spread_R); X.insert(0, "bar_age", ok.bar_age)
X.insert(0, "const", 1.0); y = ok.slip_R.values
b, *_ = np.linalg.lstsq(X.values, y, rcond=None); e = y - X.values @ b
cov = (e @ e) / (len(y) - X.shape[1]) * np.linalg.inv(X.values.T @ X.values); se = np.sqrt(np.diag(cov))
print("\npooled OLS slip_R ~ bar_age + spread_R + account:")
for k, bb, s in zip(X.columns, b, se):
    if k in ("bar_age", "spread_R", "const"): print(f"   {k:9s} {bb:+.4f} (se {s:.4f}, t {bb/s:+.1f})")
print("\nwithin-account slope of slip_R on bar_age (R per minute), controlling spread_R:")
for a, x in ok.groupby("account"):
    if len(x) < 100: continue
    Xa = np.c_[np.ones(len(x)), x.bar_age, x.spread_R]; ba, *_ = np.linalg.lstsq(Xa, x.slip_R.values, rcond=None)
    ea = x.slip_R.values - Xa @ ba; sa = np.sqrt((ea @ ea) / (len(x) - 3) * np.linalg.inv(Xa.T @ Xa)[1, 1])
    print(f"   {a:10s} n {len(x):5d}  {ba[1]:+.4f} R/min (t {ba[1]/sa:+.1f})")
slope = b[list(X.columns).index("bar_age")]
gen, oth = ok[ok.account == "Gen"].bar_age.median(), ok[ok.account != "Gen"].bar_age.median()
print(f"\nGen median bar age {gen:.2f} min vs others {oth:.2f}: at the pooled slope, Gen's extra latency costs ~{slope*(gen-oth):+.4f} R/trade")
print("Educational only - not financial advice.")
