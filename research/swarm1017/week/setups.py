"""Q3: per-setup live edge (all accounts pooled, real trades 10-06..16) vs backtest expected R.
Ranking: shrunk R = sum(r_adj)/(n+10) (descriptive). Educational only - not financial advice."""
from load import *
from mcf.report.scorecard import _expected
T = trades(); EXP = _expected()
rows = []
for s, g in T.groupby("strategy"):
    w, l = g[g.r_multiple > 0], g[g.r_multiple <= 0]
    aw, al = w.r_multiple.mean() if len(w) else np.nan, l.r_multiple.mean() if len(l) else np.nan
    be = (-al / (aw - al)) if len(w) and len(l) else np.nan
    g = g.sort_values("nt"); h = len(g) // 2
    e = EXP.get(s, EXP.get(s.replace("-FD", "")))
    rows.append(dict(setup=s, accts="/".join(sorted(g.acct.unique())), n=len(g), days=g.date.nunique(),
                     win=round(100 * g.win.mean(), 1), avg_win=round(aw, 2), avg_loss=round(al, 2),
                     be_win=round(100 * be, 1) if be == be else np.nan, avgR=round(g.r_multiple.mean(), 3),
                     avgR_adj=round(g.r_adj.mean(), 3), pnl=round(g.pnl_adj.sum(), 2), bt_R=None if e is None else round(e, 3),
                     gap=None if e is None else round(g.r_adj.mean() - e, 3),
                     first_half=round(g.r_adj.iloc[:h].mean(), 3) if h else np.nan, second_half=round(g.r_adj.iloc[h:].mean(), 3),
                     long=int((g.side == 1).sum()), short=int((g.side == -1).sum()),
                     shrunk=round(g.r_adj.sum() / (len(g) + 10), 3)))
D = pd.DataFrame(rows).sort_values("shrunk", ascending=False)
D["trend"] = np.where(D.n < 10, "n<10", np.where(D.second_half - D.first_half > 0.15, "better", np.where(D.second_half - D.first_half < -0.15, "worse", "flat")))
D.to_csv("setups_live.csv", index=False)
pd.set_option("display.width", 250)
cols = ["setup", "accts", "n", "days", "win", "avg_win", "avg_loss", "be_win", "avgR_adj", "bt_R", "first_half", "second_half", "trend", "pnl", "shrunk"]
print("setups", len(D), "with n>=10:", int((D.n >= 10).sum()), " positive avgR_adj (n>=10):", int(((D.n >= 10) & (D.avgR_adj > 0)).sum()))
print("with backtest R:", int(D.bt_R.notna().sum()), " live below backtest by >0.1R (n>=10):", int(((D.n >= 10) & (D.gap < -0.1)).sum()))
print("\nTOP 15"); print(D.head(15)[cols].to_string(index=False))
print("\nWORST 15"); print(D.tail(15)[cols].iloc[::-1].to_string(index=False))
print("\nbetter-trending n>=20:", D[(D.n >= 20) & (D.trend == "better")].setup.tolist())
print("worse-trending n>=20:", D[(D.n >= 20) & (D.trend == "worse")].setup.tolist())
# FD vs windowed pairs
print("\nsign test: share of setups (n>=10) with avgR_adj>0 by account")
for a in ACC:
    g = T[T.acct == a].groupby("strategy").r_adj.agg(["size", "mean"]); g = g[g["size"] >= 10]
    print(a, len(g), int((g["mean"] > 0).sum()))
