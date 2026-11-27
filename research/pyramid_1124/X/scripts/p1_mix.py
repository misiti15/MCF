import pandas as pd, numpy as np
X = "/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/pyramid/X/"
t = pd.read_parquet(X + "live_all.parquet"); d = pd.read_parquet(X + "live_dedup.parquet")
t = t[t.r.notna() & np.isfinite(t.r)]
t["side_s"] = np.where(t.side == 1, "long", "short")
P = t[t.account == "primary"]
pday = P.groupby("date").r.sum()
pside = P.groupby(["date", "side_s"]).r.sum().unstack().fillna(0)
print("Primary sessions", len(pday), "total R", round(pday.sum(), 1), "short share of trades", round((P.side == -1).mean(), 3))
print("Primary daily R by side: corr", round(pside.corr().iloc[0, 1], 3)); print(pside.sum().round(1))
worst = pday.nsmallest(10); print("Primary 10 worst days:\n", pd.concat([worst, pside.loc[worst.index]], axis=1).round(1))
spy = pd.read_parquet("/home/user/MCF/data/cache_fresh/spy_days.parquet") if False else None

def pools(name, g):
    m = g.groupby(["date", "side_s"]).r.mean().unstack(); n = g.groupby(["date", "side_s"]).r.size().unstack()
    s = g.groupby(["date", "side_s"]).r.sum().unstack().fillna(0)
    print(f"\n== {name}: days {len(m)}  corr(daily SUM R long, short) {s.corr().iloc[0,1]:+.3f}  corr(daily MEAN R/trade) {m.corr().iloc[0,1]:+.3f}")
    print("   corr with Primary daily R: long mean", round(m["long"].corr(pday), 3), " short mean", round(m["short"].corr(pday), 3))
    N = P.groupby("date").size().mean()
    rows = []
    for f in (0.2, 0.4, 0.6, 0.8):
        b = N * (f * m["long"] + (1 - f) * m["short"]).dropna()
        w = b.loc[b.index.isin(worst.index)]
        rows.append({"long_share": f, "days": len(b), "total": b.sum(), "mean/day": b.mean(), "sd/day": b.std(), "worst": b.min(),
                     "avg_worst5": b.nsmallest(5).mean(), "neg_days": (b < 0).mean(), "sum_on_Primary_10_worst": w.sum(),
                     "mean/sd": b.mean() / b.std()})
    print(f"   book = {N:.1f} trades/day (Primary avg) x day's mean R/trade of each side pool")
    print(pd.DataFrame(rows).round(2).to_string(index=False))
    return m
pools("ALL accounts dedup", d)
pools("Primary+Testing1+Testing2", d[d.account.isin(["primary", "testing", "testing2"])])
# sign-adjusted demo: setups that are net positive live (look-ahead; upper bound)
ps = d.groupby("strategy").r.agg(["mean", "size"]); good = ps[(ps["mean"] > 0) & (ps["size"] >= 20)].index
pools("live-positive setups only (look-ahead, illustrative)", d[d.strategy.isin(good)])
print("positive setups by side:", d[d.strategy.isin(good)].drop_duplicates("strategy").side_s.value_counts().to_dict())
# lab mix
L = pd.read_csv(X + "lab_side_daily.csv", index_col=0)
for h, g in L.groupby(np.where(L.index < "2025-10-01", "FIT", "CHECK")):
    rows = []
    for f in (0.2, 0.4, 0.6, 0.8):
        b = 10 * (f * g["long"] + (1 - f) * g["short"])
        rows.append({"long_share": f, "total": b.sum(), "mean/day": b.mean(), "sd": b.std(), "worst": b.min(), "avg_worst5": b.nsmallest(5).mean(), "neg_days": (b < 0).mean()})
    print(f"\nLAB {h} ({len(g)} days, 10 trades/day, setup-equal-weight daily mean R per side)\n", pd.DataFrame(rows).round(2).to_string(index=False))
