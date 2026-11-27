import pandas as pd, numpy as np
X = "/tmp/claude-0/-home-user/9c6fc50d-b94d-5471-ba1f-4c82eb058810/scratchpad/pyramid/X/"
t = pd.read_parquet(X + "live_all.parquet"); d = pd.read_parquet(X + "live_dedup.parquet")
t = t[t.r.notna() & np.isfinite(t.r)]; t["side_s"] = np.where(t.side == 1, "long", "short")
spy = pd.read_csv(X + "spy_live_days.csv", index_col=0)
P = t[t.account == "primary"]; pday = P.groupby("date").r.sum(); worst = pday.nsmallest(10).index
# SPY day type split
for nm, g in (("ALL dedup", d), ("P+T1+T2", d[d.account.isin(["primary", "testing", "testing2"])]), ("Primary", P)):
    g = g.assign(ty=g.date.map(spy["type"]))
    print(nm, "avg R per trade by SPY day type (n)"); print(g.pivot_table(index="ty", columns="side_s", values="r", aggfunc=["mean", "size"]).round(3))
print("SPY day types:", spy["type"].value_counts().to_dict())
# Primary swap: Primary's own short trades' daily mean R + long pool (P+T1+T2 longs) daily mean R
N = P.groupby("date").size().mean()
ps = P[P.side == -1].groupby("date").r.mean()
for nm, lp in (("P+T1+T2 longs (all)", d[d.account.isin(["primary", "testing", "testing2"]) & (d.side == 1)]),
               ("Primary's own longs", P[P.side == 1])):
    lm = lp.groupby("date").r.mean()
    j = pd.concat([ps.rename("S"), lm.rename("L")], axis=1).dropna()
    rows = []
    for f in (0.2, 0.4, 0.6):
        b = N * (f * j.L + (1 - f) * j.S)
        rows.append({"long_share": f, "days": len(b), "total": b.sum(), "mean": b.mean(), "sd": b.std(), "worst": b.min(),
                     "avg_worst5": b.nsmallest(5).mean(), "on_P10worst": b[b.index.isin(worst)].sum(), "neg_days": (b < 0).mean()})
    print(f"\nPrimary short book + {nm}: corr(S,L) {j.S.corr(j.L):+.3f}, {N:.1f} trades/day"); print(pd.DataFrame(rows).round(2).to_string(index=False))
# ticker concentration
for nm, g in (("Primary", P), ("P+T1+T2", d[d.account.isin(["primary", "testing", "testing2"])]), ("ALL", d)):
    for s, h in g.groupby("side_s"):
        vc = h.symbol.value_counts(); top10 = vc.head(10).sum() / len(h)
        sd = h.groupby("symbol").date.nunique()
        print(f"{nm:8s} {s:5s} trades {len(h):6d} symbols {len(vc):5d} trades/symbol {len(h)/len(vc):5.2f} top10 share {top10:.3f}  symbols traded on >=5 days {int((sd>=5).sum())} ({(h.symbol.isin(sd[sd>=5].index)).mean():.2f} of trades)  top: {', '.join(vc.head(6).index)}")
# same-ticker repeat across days in Primary shorts
ps_sym = P[P.side == -1].groupby("date").symbol.apply(set)
rep = [len(ps_sym.iloc[i] & set().union(*ps_sym.iloc[max(0, i-5):i])) / max(1, len(ps_sym.iloc[i])) for i in range(1, len(ps_sym))]
print("Primary shorts: share of a day's short symbols already shorted in the prior 5 sessions:", round(np.mean(rep), 3))
pl_sym = d[d.account.isin(["primary","testing","testing2"]) & (d.side==1)].groupby("date").symbol.apply(set)
rep = [len(pl_sym.iloc[i] & set().union(*pl_sym.iloc[max(0, i-5):i])) / max(1, len(pl_sym.iloc[i])) for i in range(1, len(pl_sym))]
print("P+T1+T2 longs: same metric:", round(np.mean(rep), 3))
ps_sym = d[d.account.isin(["primary","testing","testing2"]) & (d.side==-1)].groupby("date").symbol.apply(set)
rep = [len(ps_sym.iloc[i] & set().union(*ps_sym.iloc[max(0, i-5):i])) / max(1, len(ps_sym.iloc[i])) for i in range(1, len(ps_sym))]
print("P+T1+T2 shorts: same metric:", round(np.mean(rep), 3))
