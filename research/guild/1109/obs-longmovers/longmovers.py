"""Observer: our LONG trades vs the Move Hunt LONG movers (tradable set, 10-29..11-05). Journals only, 0 configs, descriptive.
Window as research/bdi/moves/moves.py: caught = long entry between decision-30 min and the extreme.
usage (from the MCF checkout): python longmovers.py <journal_dir>. Educational only - not financial advice."""
import sys, sqlite3, glob, os
import numpy as np, pandas as pd
J = sys.argv[1]; TZ = "America/New_York"
M = pd.read_csv("research/bdi/moves/moves.csv"); M = M[(M.set == "tradable") & (M.side == "long")].copy()
T, G = [], []
for f in sorted(glob.glob(os.path.join(J, "*.db"))):
    a = os.path.basename(f).replace("mcf-data-", "").replace(".db", "").replace("journal", "primary")
    c = sqlite3.connect(f)
    t = pd.read_sql("select date, symbol, strategy, side, entry_time, entry, stop, shares, pnl_adj, mfe_r from trades where run_id=1", c); t["acct"] = a; T.append(t)
    g = pd.read_sql("select day as date, symbol, strategy, side, ts, status, reason from signals where run_id=1 and side=1", c); g["acct"] = a; G.append(g)
T = pd.concat(T); T = T[T.date.isin(M.date.unique())]; G = pd.concat(G); G = G[G.date.isin(M.date.unique())]
for X, col in ((T, "entry_time"), (G, "ts")):
    e = pd.to_datetime(X[col], utc=True, format="mixed").dt.tz_convert(TZ); X["m"] = e.dt.hour * 60 + e.dt.minute - 570 + e.dt.second / 60
T["R"] = T.pnl_adj / ((T.entry - T.stop).abs() * T.shares).replace(0, np.nan)
mm = lambda s: (int(s[:2]) - 9) * 60 + int(s[3:]) - 30
M["m0"] = M.decision.map(mm); M["m1"] = M.extreme.map(mm)
rows, caught = [], []
for _, r in M.iterrows():
    L = T[(T.date == r.date) & (T.symbol == r.symbol) & (T.side == 1)]
    S = G[(G.date == r.date) & (G.symbol == r.symbol)]
    win = L[(L.m >= r.m0 - 30) & (L.m <= r.m1)]
    if len(win):
        f = win.sort_values("m").iloc[0]
        caught.append(win.assign(lag=win.m - r.m0, frac=(win.m - r.m0) / max(r.m1 - r.m0, 1), move_atr=r.move_atr))
    rows.append(dict(date=r.date, symbol=r.symbol, dec=r.decision, ext=r.extreme, move_atr=r.move_atr,
                     caught=len(win) > 0, first_lag=(win.m.min() - r.m0) if len(win) else np.nan,
                     n_long_after=int((L.m > r.m1).sum()), n_long_before=int((L.m < r.m0 - 30).sum()),
                     long_sig_window=int(((S.m >= r.m0 - 30) & (S.m <= r.m1)).sum()),
                     early_shadow=int(((S.m < 20) & (S.status != "submitted")).sum()),
                     **{k: r[k] for k in ["gap", "fromOpen", "vwapDistPct", "rsi", "rvol", "dist_hod_atr", "atr_pct_d", "adv_musd", "mae_before_atr"]}))
D = pd.DataFrame(rows); C = pd.concat(caught) if caught else pd.DataFrame()
print(f"long movers {len(D)}; caught {int(D.caught.sum())} ({D.caught.mean():.0%}); long trades in window {len(C)} R {C.R.sum():+.2f} avg {C.R.mean():+.2f}")
print(f"caught movers: median move {D[D.caught].move_atr.median():.2f} ATR vs missed {D[~D.caught].move_atr.median():.2f}")
print("\nby decision bucket:"); D["bucket"] = np.where(D.dec == "09:35", "09:35", "later")
print(D.groupby("bucket").agg(n=("caught", "size"), caught=("caught", "sum")).to_string())
print("\ncaught trades: entry minutes after the move's decision bar (neg = before):", C.lag.describe().round(1).to_dict())
print("caught trades: fraction of decision->extreme elapsed at entry:", C.frac.describe().round(2).to_dict())
print("  R by entry fraction:", C.groupby(pd.cut(C.frac, [-9, 0, .25, .5, 1.01])).R.agg(["count", "sum", "mean"]).round(2).to_dict("index"))
print("\ncatchers by account:\n", C.groupby("acct").R.agg(["count", "sum", "mean"]).round(2).to_string())
print("\ncatchers by setup:\n", C.groupby("strategy").agg(n=("R", "size"), R=("R", "sum"), movers=("symbol", "nunique"), lag_med=("lag", "median"), mfe_med=("mfe_r", "median")).sort_values("n", ascending=False).round(2).to_string())
print("\nmissed movers: long trades on the symbol that day only AFTER the extreme:", int(((~D.caught) & (D.n_long_after > 0)).sum()),
      "| only BEFORE window:", int(((~D.caught) & (D.n_long_before > 0) & (D.n_long_after == 0)).sum()),
      "| any long signal in window but not filled:", int(((~D.caught) & (D.long_sig_window > 0)).sum()))
print("\nfeatures at the decision bar (median), caught vs missed (ex ante, from moves.csv):")
print(D.groupby("caught")[["gap", "fromOpen", "vwapDistPct", "rsi", "rvol", "dist_hod_atr", "atr_pct_d", "adv_musd", "mae_before_atr", "move_atr"]].median().round(2).T.to_string())
print("\nby date:", D.groupby("date").caught.agg(["size", "sum"]).to_dict("index"))
# late longs: long trades on a long mover entered after its extreme
late = []
for _, r in M.iterrows():
    L = T[(T.date == r.date) & (T.symbol == r.symbol) & (T.side == 1) & (T.m > r.m1)]
    late.append(L.assign(after=L.m - r.m1))
late = pd.concat(late)
print(f"\nlong trades entered AFTER the mover's extreme: {len(late)} R {late.R.sum():+.2f} avg {late.R.mean():+.2f}; median minutes after extreme {late.after.median():.0f}")
print(late.groupby("acct").R.agg(["count", "sum"]).round(2).to_string())
print("top setups:", late.groupby("strategy").R.agg(["count", "sum"]).sort_values("count", ascending=False).head(6).round(2).to_string())
