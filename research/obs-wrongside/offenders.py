"""Observer: which live setups own the wrong-direction trades on Move Hunt movers (tradable set, 10-29..11-05).
Same window as research/bdi/moves/moves.py: entry between decision-30 min and the extreme, opposite side, run_id=1.
Journals: journal.db from each mcf-data* branch (pass the dir). Descriptive, 0 configs. Educational only - not financial advice.
usage: python offenders.py <journal_dir>   (run from the MCF checkout)"""
import sys, sqlite3, glob, os
import numpy as np, pandas as pd
J = sys.argv[1]; TZ = "America/New_York"
M = pd.read_csv("research/bdi/moves/moves.csv"); M = M[M.set == "tradable"]
T = []
for f in sorted(glob.glob(os.path.join(J, "*.db"))):
    a = os.path.basename(f).replace("mcf-data-", "").replace(".db", "").replace("journal", "primary")
    t = pd.read_sql("select date, symbol, strategy, side, entry_time, entry, stop, shares, pnl_adj from trades where run_id=1",
                    sqlite3.connect(f)); t["acct"] = a; T.append(t)
T = pd.concat(T); T = T[T.date.isin(M.date.unique())]
T["et"] = pd.to_datetime(T.entry_time, utc=True, format="mixed").dt.tz_convert(TZ)
T["m"] = T.et.dt.hour * 60 + T.et.dt.minute - 570 + T.et.dt.second / 60
T["R"] = T.pnl_adj / ((T.entry - T.stop).abs() * T.shares).replace(0, np.nan)
mm = lambda s: (int(s[:2]) - 9) * 60 + int(s[3:]) - 30
W, Rt = [], []
for _, r in M.iterrows():
    sgn = 1 if r.side == "long" else -1; m0, m1 = mm(r.decision), mm(r.extreme)
    x = T[(T.date == r.date) & (T.symbol == r.symbol) & (T.m >= m0 - 30) & (T.m <= m1)]
    w = x[x.side == -sgn].assign(move_side=r.side, move_atr=r.move_atr, dec=r.decision, early=(x.m < m0))
    W.append(w); Rt.append(x[x.side == sgn])
W = pd.concat(W); Rt = pd.concat(Rt)
print(f"wrong-direction trades {len(W)} R {W.R.sum():+.2f} | right-direction {len(Rt)} R {Rt.R.sum():+.2f}")
print(f"wrong entered BEFORE the move's decision bar (in the 30-min lookback): {int(W.early.sum())} R {W[W.early].R.sum():+.2f}")
print("\nby account:\n", W.groupby("acct").R.agg(["count", "sum", "mean"]).round(2).sort_values("sum").to_string())
g = W.groupby(["strategy"]).agg(n=("R", "size"), R=("R", "sum"), avg=("R", "mean"), days=("date", "nunique"),
                                accts=("acct", lambda s: ",".join(sorted(set(s))))).sort_values("R")
base = T.groupby("strategy").R.agg(all_n="size", all_R="sum", all_avg="mean")
g = g.join(base); g["share_of_wrongR"] = (g.R / W.R.sum()).round(3)
g["cum_share"] = g.share_of_wrongR.cumsum().round(2)
print("\nby setup (all 6 days, all accounts; all_* = every trade of that setup on those 6 days):\n", g.round(2).to_string())
print("\nby move side x day:\n", W.groupby(["date", "move_side"]).R.agg(["count", "sum"]).round(2).to_string())
best = W.groupby("date").R.sum(); print(f"\nworst day share of wrong R: {best.min():+.2f} on {best.idxmin()} = {best.min()/W.R.sum():.0%}")
