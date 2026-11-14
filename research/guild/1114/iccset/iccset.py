"""ICCSET - same-day correlation (ICC) per setup, and the effective number of independent trades it implies (descriptive, 0 configs).
Live paper trades 10-20..11-11, 7 journals, net R (pnl_adj / risk). Per setup with >= 40 trades on >= 8 days: one-way random-effects
ICC(1) with day as the group (ANOVA estimator, unbalanced k0); n_eff = n / (1 + (m - 1) x ICC), m = mean trades per day.
Also: ICC vs the setup's market beta (daily mean R on SPY o->c, from BOTHDAYS' SPY file) and vs trades/day.
    python -I iccset.py <journal dir> <spy_daily.csv>        Educational only - not financial advice."""
import sys, glob, os, sqlite3, numpy as np, pandas as pd
R = []
for p in sorted(glob.glob(f"{sys.argv[1]}/mcf-data*.db")):
    if os.path.getsize(p) == 0: continue
    c = sqlite3.connect(p); pid = ",".join(str(r[0]) for r in c.execute("select id from runs where kind='paper'"))
    t = pd.read_sql(f"select strategy, date, side, entry, stop, shares, pnl_adj from trades where run_id in ({pid}) and pnl_adj is not null "
                    f"and date >= '2026-10-20' and date <= '2026-11-11'", c); t["acct"] = os.path.basename(p)[:-3]; R.append(t)
T = pd.concat(R, ignore_index=True); T["risk"] = (T.entry - T.stop).abs() * T.shares; T = T[T.risk > 0]; T["R"] = T.pnl_adj / T.risk
T["R"] = T.R.clip(-3, 6)                                   # winsorise a few extreme fills so one trade does not drive an ICC
def icc1(g):
    d = g.groupby("date").R; n_i = d.size(); k = len(n_i); N = n_i.sum()
    if k < 2 or N <= k: return np.nan
    grand = g.R.mean(); msb = (n_i * (d.mean() - grand) ** 2).sum() / (k - 1)
    msw = ((g.R - g.date.map(d.mean())) ** 2).sum() / (N - k)
    k0 = (N - (n_i ** 2).sum() / N) / (k - 1)
    return (msb - msw) / (msb + (k0 - 1) * msw)
S = pd.read_csv(sys.argv[2]); S["oc"] = (S.c / S.o - 1) * 100; spy = S.set_index("date").oc
rows = []
for s, g in T.groupby("strategy"):
    if len(g) < 40 or g.date.nunique() < 8: continue
    icc = icc1(g); m = len(g) / g.date.nunique()
    dm = g.groupby("date").R.mean(); x = spy.reindex(dm.index)
    beta = np.polyfit(x.dropna(), dm[x.notna()], 1)[0] if x.notna().sum() >= 5 else np.nan
    rows.append(dict(setup=s, n=len(g), days=g.date.nunique(), per_day=m, icc=icc, n_eff=len(g) / (1 + (m - 1) * max(icc, 0)),
                     side=float((g.side > 0).mean()), beta=beta, avgR=g.R.mean()))
D = pd.DataFrame(rows).sort_values("icc")
print(f"setups with >= 40 trades on >= 8 days: {len(D)} (of {T.strategy.nunique()}); pooled-style median ICC {D.icc.median():.3f}")
print(f"ICC quartiles: {D.icc.quantile([.1,.25,.5,.75,.9]).round(3).to_dict()}")
print(f"n_eff / n: median {(D.n_eff / D.n).median():.2f}; setups whose n_eff < 2 x days: {int((D.n_eff < 2 * D.days).sum())}")
print(f"corr(ICC, |beta|) {D.icc.corr(D.beta.abs()):.2f}; corr(ICC, trades/day) {D.icc.corr(D.per_day):.2f}; "
      f"median ICC longs {D[D.side > .5].icc.median():.3f} vs shorts {D[D.side <= .5].icc.median():.3f}")
# null check: shuffle R across days within setup -> ICC should centre on ~0
rng = np.random.default_rng(1); nul = []
for s, g in T[T.strategy.isin(D.setup)].groupby("strategy"):
    g = g.copy(); g["R"] = rng.permutation(g.R.values); nul.append(icc1(g))
print(f"null (R shuffled across days within setup): median ICC {np.nanmedian(nul):+.3f}, 90th pct {np.nanpercentile(nul, 90):+.3f}")
pd.set_option("display.width", 200)
c = ["setup", "n", "days", "per_day", "icc", "n_eff", "side", "beta", "avgR"]
print("\nlowest ICC (records worth the most per trade):"); print(D[c].head(10).round(3).to_string(index=False))
print("\nhighest ICC (records worth ~one trade per day):"); print(D[c].tail(10).round(3).to_string(index=False))
D.to_csv("iccset_setups.csv", index=False); print("Educational only - not financial advice.")
