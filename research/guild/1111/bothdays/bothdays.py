"""BOTHDAYS (descriptive, 0 configs; follows Builder's lab join builder-20261111-0040-1 and Lead lead-20261111-0100-1).
Live 'what works' is a market-direction bet. Question here: which live setups earn on BOTH SPY up and SPY down sessions?
Per setup (pooled over accounts, live paper run only, 7 journals, to 11-10): avg R on SPY up days vs down days
(SPY 09:30 open -> 16:00 close, Alpaca daily bar), and the intercept of daily setup R/trade on SPY o->c return
(direction-free part; slope = market beta in R per 1% SPY). Gate (descriptive): n >= 10 trades on each day type,
avg R > 0 on both, and avg w/o best day > 0 on both.
    python -I bothdays.py <dir with mcf-data*.db> <out dir>      Educational only - not financial advice."""
import sys, os, json, sqlite3, glob, urllib.request
import numpy as np, pandas as pd
DIR, OUT = sys.argv[1], sys.argv[2]
ACCT = {"mcf-data": "primary", "mcf-data-testing": "testing", "mcf-data-testing2": "testing2", "mcf-data-graveyard": "graveyard",
        "mcf-data-gen": "gen", "mcf-data-explore1": "explore1", "mcf-data-livelab": "livelab"}
rows = []
for p in sorted(glob.glob(f"{DIR}/mcf-data*.db")):
    acct = ACCT[os.path.basename(p)[:-3]]; c = sqlite3.connect(p)
    pid = [r[0] for r in c.execute("select id from runs where kind='paper'")]
    if not pid: continue
    t = pd.read_sql(f"select strategy, symbol, date, side, entry, stop, shares, pnl_adj from trades where run_id in ({','.join(map(str, pid))}) and pnl_adj is not null", c)
    t["risk"] = (t.entry - t.stop).abs() * t.shares; t = t[(t.risk > 0) & (t.date <= "2026-11-10")]
    t["R"] = t.pnl_adj / t.risk; t["account"] = acct; rows.append(t)
T = pd.concat(rows, ignore_index=True)
spy_f = f"{OUT}/spy_daily.csv"
if not os.path.exists(spy_f):
    url = (f"https://data.alpaca.markets/v2/stocks/SPY/bars?timeframe=1Day&start={T.date.min()}&end=2026-11-10"
           "&adjustment=raw&feed=sip&limit=1000")
    req = urllib.request.Request(url, headers={"APCA-API-KEY-ID": os.environ["ALPACA_API_KEY"],
                                               "APCA-API-SECRET-KEY": os.environ["ALPACA_SECRET_KEY"]})
    bars = json.load(urllib.request.urlopen(req, timeout=30))["bars"]
    pd.DataFrame([dict(date=b["t"][:10], o=b["o"], c=b["c"]) for b in bars]).to_csv(spy_f, index=False)
S = pd.read_csv(spy_f); S["oc"] = (S.c / S.o - 1) * 100
miss = sorted(set(T.date) - set(S.date)); assert not miss, miss
T = T.merge(S[["date", "oc"]], on="date"); T["up"] = T.oc > 0
nu, nd = int((S.oc > 0).sum()), int((S.oc <= 0).sum())
print(f"live paper trades {len(T)}, {T.strategy.nunique()} setups, {T.date.min()}..{T.date.max()}; SPY o->c up days {nu}, down days {nd}")
def wob(g):
    if len(g) == 0: return np.nan
    gd = g.groupby("date").R.sum(); b = gd.idxmax()
    rest = len(g) - int((g.date == b).sum())
    return (gd.sum() - gd.max()) / rest if rest else np.nan
res = []
for s, g in T.groupby("strategy"):
    u, d = g[g.up], g[~g.up]
    day = g.groupby("date").agg(R=("R", "mean"), oc=("oc", "first"))
    if len(day) >= 5:
        X = np.c_[np.ones(len(day)), day.oc]; b, *_ = np.linalg.lstsq(X, day.R.values, rcond=None)
        e = day.R.values - X @ b; se = np.sqrt((e @ e) / max(1, len(day) - 2) * np.linalg.inv(X.T @ X)[0, 0])
        icpt, beta, t_i = b[0], b[1], b[0] / se if se > 0 else np.nan
    else: icpt = beta = t_i = np.nan
    res.append(dict(setup=s, accounts="/".join(sorted(g.account.unique())), n=len(g), days=g.date.nunique(),
                    long_share=round(float((g.side > 0).mean()), 2), avg=g.R.mean(),
                    n_up=len(u), avg_up=u.R.mean(), wob_up=wob(u), n_dn=len(d), avg_dn=d.R.mean(), wob_dn=wob(d),
                    icpt=icpt, t_icpt=t_i, beta=beta))
R = pd.DataFrame(res).sort_values("icpt", ascending=False); R.to_csv(f"{OUT}/bothdays_all.csv", index=False)
E = R[(R.n_up >= 10) & (R.n_dn >= 10)]
P = E[(E.avg_up > 0) & (E.avg_dn > 0) & (E.wob_up > 0) & (E.wob_dn > 0)]
print(f"setups with >= 10 trades on each day type: {len(E)} (long-only {int((E.long_share==1).sum())}, short-only {int((E.long_share==0).sum())})")
print(f"  positive on up days: {int((E.avg_up>0).sum())}; positive on down days: {int((E.avg_dn>0).sum())}; both: {int(((E.avg_up>0)&(E.avg_dn>0)).sum())}; both incl. w/o best day: {len(P)}")
print(f"  median beta (R per 1% SPY o->c): longs {E[E.long_share==1].beta.median():+.3f}, shorts {E[E.long_share==0].beta.median():+.3f}")
print(f"  intercept > 0: {int((E.icpt>0).sum())}; intercept t >= 2: {int((E.t_icpt>=2).sum())} (expected by chance at 5% one-sided ~{0.05*len(E):.1f})")
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30)
cols = ["setup", "accounts", "n", "days", "long_share", "avg", "n_up", "avg_up", "wob_up", "n_dn", "avg_dn", "wob_dn", "icpt", "t_icpt", "beta"]
print("\nBOTH-DAY setups (descriptive gate):"); print(P[cols].round(3).to_string(index=False))
print("\nTop 12 by intercept (direction-free part), any:"); print(E[cols].head(12).round(3).to_string(index=False))
print("\nEducational only - not financial advice.")
