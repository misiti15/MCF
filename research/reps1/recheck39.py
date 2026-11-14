"""REPS1b re-check under checklist #39: pooled ratio estimator with day-clustered SE instead of averaging per-day group means.
Per group (Gen / low-rep / other) x lever: estimate = sum over days of (adj what-if - base live gross) / count; SE from per-day
residual sums (cluster-robust ratio SE). Base = the group's submitted live gross per trade (pooled, constant), as in REPS1b's
adj_vs_live. Educational only - not financial advice.
    python -I recheck39.py <reps1_signals_sim.csv.gz> <trades.csv.gz>"""
import sys, numpy as np, pandas as pd
S = pd.read_csv(sys.argv[1]); T = pd.read_csv(sys.argv[2])
S["hr"] = pd.to_datetime(S.ts, utc=True).dt.tz_convert("America/New_York").dt.hour.clip(9, 15)
T["k"] = T.acct + "|" + T.strategy + "|" + T.symbol + "|" + T.date
T["risk"] = (T.entry - T.stop).abs() * T.shares; T = T[T.risk > 0]; T["gR"] = T.pnl / T.risk
S["k"] = S.acct + "|" + S.strategy + "|" + S.symbol + "|" + S.day
C = S[S.status == "submitted"].drop_duplicates("k").join(T.groupby("k").gR.mean(), on="k").dropna(subset=["sim", "gR"])
gap = (C.sim - C.gR).groupby(C.hr).mean(); S["adj"] = S.sim - S.hr.map(gap)
def ratio(x, base):
    y = x.adj - base; g = y.groupby(x.day); s, n = g.sum(), g.size()
    est = s.sum() / n.sum(); res = s - est * n; k = len(n)
    se = np.sqrt(k / (k - 1) * (res ** 2).sum()) / n.sum() if k > 1 else np.nan
    return est, est / se if se and se > 0 else np.nan, k
print("group      lever                               n   days  pooled est   pooled t   (REPS1b per-day-mean t)")
old = {("Gen", "account halt"): "NaN (2 days)", ("Gen", "buying power"): "1.71", ("Gen", "spread filters (bps / % of stop)"): "0.94",
       ("low-rep", "borrow: not shortable / ETB"): "-2.38", ("low-rep", "spread filters (bps / % of stop)"): "1.38",
       ("low-rep", "symbol conflict / twin block"): "-1.33", ("other", "borrow: not shortable / ETB"): "2.83"}
for grp in ("Gen", "low-rep", "other"):
    base = C[C.grp == grp].gR.mean()
    for lv, x in S[(S.grp == grp) & (S.status != "submitted")].dropna(subset=["adj"]).groupby("lever"):
        if len(x) < 30: continue
        est, t, k = ratio(x, base)
        print(f"{grp:9s}  {lv[:34]:34s} {len(x):5d} {k:4d}   {est:+.3f}     {t:+6.2f}     {old.get((grp, lv), '')}")
print("Educational only - not financial advice.")
