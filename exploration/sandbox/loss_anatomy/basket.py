"""Basket anatomy + robustness of the per-setup-day lot cap: basket-size table, half-size variant, split halves,
ex-11-25, U-control tail metrics, per-family effect. Usage: python basket.py <scratch>. Educational only - not financial advice."""
import sys, numpy as np, pandas as pd
from common import dayt, summ
S = sys.argv[1]; rng = np.random.default_rng(11)
f = pd.read_parquet(f"{S}/feat2.parquet")
f["sd_n"] = f.groupby(["account", "date", "strategy"]).r.transform("size")
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30)
for book in ["primary", "arena"]:
    x = f[f.book == book].reset_index(drop=True)
    print("=====", book)
    x["nb"] = pd.cut(x.sd_n, [0, 1, 3, 5, 10, 20, 50, 1e5])
    t = x.groupby("nb", observed=True).apply(lambda g: pd.Series({"setup_days": g.groupby(["account", "date", "strategy"]).ngroups,
        "lots": len(g), "R": g.r.sum(), "avgR": g.r.mean(), "stop%": 100 * (g.exit_reason == "stop").mean(), "days": g.date.nunique(), "R_wo_best": g.r.sum() - g.groupby("date").r.sum().max()}))
    t["R%"] = 100 * t.R / x.r.sum(); print(t.round(2))
    base = x.groupby("date").r.sum(); wk = len(base) / 5
    for K in [5, 10]:
        for mode in ["skip", "half"]:
            w = np.where(x.sd_lot <= K, 1.0, 0.0 if mode == "skip" else 0.5)
            new = (x.r * w).groupby(x.date).sum(); d = new - base
            # U control with same removed exposure (sum of 1-w)
            ex = (1 - w).sum(); uw = []; u5 = []; ured = []; ug = []
            for _ in range(200):
                m = np.ones(len(x)); k = int(round(ex)); m[rng.choice(len(x), k, replace=False)] = 0.0
                un = (x.r * m).groupby(x.date).sum(); uw.append(un.sum() - base.sum()); u5.append(un.nsmallest(5).sum()); ured.append((un <= 0).sum()); ug.append((un - base)[base > 0].sum())
            h1 = d[d.index < "2026-11-11"].sum(); h2 = d[d.index >= "2026-11-11"].sum()
            print(f"K{K} {mode}: exposure cut {100*ex/len(x):.0f}%  saved {d.sum():+.1f}R ({d.sum()/wk:+.1f}/wk; U ctrl {np.mean(uw):+.1f}, pct {100*np.mean(np.array(uw)<d.sum()):.0f})  "
                  f"ex-11-25 {d.drop('2026-11-25', errors='ignore').sum():+.1f}  halves {h1:+.1f} / {h2:+.1f}  days improved {(d>0).sum()}/{(d!=0).sum()}  dt {dayt(d):.2f}  "
                  f"green-day cost {d[base>0].sum():+.1f} (U {np.mean(ug):+.1f})  worst5 {base.nsmallest(5).sum():.1f}->{new.nsmallest(5).sum():.1f} (U {np.mean(u5):.1f})  "
                  f"red {int((base<=0).sum())}->{int((new<=0).sum())} (U {np.mean(ured):.1f})  worst day {base.min():.1f}->{new.min():.1f}  best-day share {d.max()/d.sum():.2f}")
            if K == 5 and mode == "half":
                fam = pd.DataFrame({"fam": x.family, "d": x.r * w - x.r}).groupby("fam").d.sum()
                fam = fam[fam != 0].sort_values()
                print(f"   families better {int((fam>0).sum())} worse {int((fam<0).sum())} worse sum {fam[fam<0].sum():+.1f}; worst: {fam.head(4).round(1).to_dict()}; best: {fam.tail(4).round(1).to_dict()}")
                st = pd.DataFrame({"s": x.strategy, "d": x.r * w - x.r}).groupby("s").d.sum(); st = st[st != 0]
                print(f"   setups better {int((st>0).sum())} worse {int((st<0).sum())} worse sum {st[st<0].sum():+.1f} (median worse {st[st<0].median():+.2f}); biggest losers from cap: {st.nsmallest(3).round(1).to_dict()}")
