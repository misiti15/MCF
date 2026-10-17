"""Q1/Q2: account-level week vs week and last-3 vs prior-3. Educational only - not financial advice."""
from load import *
T = trades()
def agg(g):
    return pd.Series({"n": len(g), "win%": round(100 * g.win.mean(), 1), "avgR": round(g.r_multiple.mean(), 3),
                      "avgR_adj": round(g.r_adj.mean(), 3), "pnl": round(g.pnl.sum(), 2), "pnl_adj": round(g.pnl_adj.sum(), 2),
                      "long_pnl": round(g[g.side == 1].pnl.sum(), 2), "short_pnl": round(g[g.side == -1].pnl.sum(), 2)})
print("== index open->close % per day")
for d in LAST + THIS: print(d, index_day(d))
print("\n== per account per day (journal) + broker day P/L (closed - pre-open)")
for a in ACC:
    x = T[T.acct == a].groupby("date").apply(agg)
    x["broker"] = [round(EQ[a][d][1] - EQ[a][d][0], 2) if d in EQ[a] else None for d in x.index]
    print(ACC[a]); print(x.to_string())
def per(days, lab):
    x = T[T.date.isin(days)].groupby("acct").apply(agg)
    x["broker"] = [round(sum(EQ[a][d][1] - EQ[a][d][0] for d in days if d in EQ[a]), 2) for a in x.index]
    x["sessions"] = [sum(d in EQ[a] for d in days) for a in x.index]
    x["pnl/session"] = (x.pnl / x.sessions).round(2)
    print(f"\n== {lab}"); print(x.to_string())
per(LAST, "LAST WEEK 10-06..10-09"); per(THIS, "THIS WEEK 10-12..10-16")
per(P3, "PRIOR 3 (10-09,12,13)"); per(L3, "LAST 3 (10-14..16)")
# same-setup like-for-like: Primary setups that ran both weeks
print("\n== Primary per setup last week vs this week")
p = T[T.acct == "p"]
lw = p[p.date.isin(LAST)].groupby("strategy").apply(agg); tw = p[p.date.isin(THIS)].groupby("strategy").apply(agg)
print(lw[["n", "win%", "avgR", "pnl"]].join(tw[["n", "win%", "avgR", "pnl"]], lsuffix="_lw", rsuffix="_tw", how="outer").to_string())
print("\n== T1 per setup P3 vs L3 (n>=5 both)")
for a in ("t1", "t2"):
    q = T[T.acct == a]
    x = q[q.date.isin(P3)].groupby("strategy").apply(agg)[["n", "avgR", "pnl"]].join(q[q.date.isin(L3)].groupby("strategy").apply(agg)[["n", "avgR", "pnl"]], lsuffix="_p3", rsuffix="_l3", how="inner")
    x = x[(x.n_p3 >= 5) & (x.n_l3 >= 5)]; print(a, "same-setup", len(x), "improved avgR:", int((x.avgR_l3 > x.avgR_p3).sum()))
    print(" totals same setups p3 pnl", round(x.pnl_p3.sum(), 2), "l3 pnl", round(x.pnl_l3.sum(), 2))
