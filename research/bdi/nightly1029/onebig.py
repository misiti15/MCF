"""One-big-day detail for tonight's candidates and monitor marks (all accounts merged, real trades, costs in:
R = pnl_adj / $ risk). Per-session R, avg R without the best 1 and 2 sessions, record since a given date.
Usage: python onebig.py <scratch>   Educational only - not financial advice."""
import sys, sqlite3
from pathlib import Path
import numpy as np, pandas as pd
S = Path(sys.argv[1]); OUT = Path(__file__).resolve().parent
rows = []
for a in ("p", "t1", "t2", "gy", "gen"):
    c = sqlite3.connect(S / a / "journal.db")
    t = pd.read_sql("select date, strategy, entry, stop, shares, pnl, pnl_adj, r_multiple from trades where run_id=1 and exit is not null", c)
    t["acct"] = a; rows.append(t)
T = pd.concat(rows); T["pnl_adj"] = T.pnl_adj.fillna(T.pnl)
T["risk"] = (T.entry - T.stop).abs() * T.shares; T["rc"] = np.where(T.risk > 0, T.pnl_adj / T.risk, T.r_multiple)
W = {"L3-gap-slope-fromopen-FD": None, "L3-gap-slope-rsi5hi-FD": None, "exhaustion_short-FD": None,
     "NS4-pm-vwap-reclaim-oversold-short-FD": "2026-10-28", "GEN-261026-03-NewLOD-Flow3lem0p37-FromOpenATRlem0p78-LUNCH-BRopgt0p5-holdtr-short": "2026-10-28",
     "CWT14-failbrk-pdl-p10-lowvol-long": "2026-10-28", "CWT14-failbrk-pdl-p05-long": "2026-10-29", "CWT14-failbrk-pdl-p05-lowvol-long": "2026-10-29",
     "CWT14-failbrk-pdl-p10-long": "2026-10-29", "GEN-261020-07-RSIslopege19-LowWickge0p33-ATRdge4p4-AM-BRvwgt0p7-hold-long": None}
out = []
for s, since in W.items():
    g = T[T.strategy == s]; d = g.groupby("date").agg(n=("rc", "size"), R=("rc", "sum"), usd=("pnl_adj", "sum"))
    top = d.R.sort_values(ascending=False)
    ex1 = (d.R.sum() - top.iloc[0]) / (len(g) - d.n[top.index[0]]) if len(d) > 1 else np.nan
    ex2 = (d.R.sum() - top.iloc[:2].sum()) / (len(g) - d.n[top.index[:2]].sum()) if len(d) > 2 else np.nan
    w = (g.pnl > 0).mean(); r = g.r_multiple; aw, al = r[r > 0].mean(), -r[r <= 0].mean()
    out.append(f"\n== {s}: {len(g)} trades / {len(d)} sessions, win {w:.1%} vs be {al/(aw+al):.1%}, avgR {g.rc.mean():+.3f}, "
               f"w/o best day {ex1:+.3f} (best {top.index[0]} {top.iloc[0]:+.2f}R = {top.iloc[0]/d.R.sum():.0%} of {d.R.sum():+.2f}R), "
               f"w/o best 2 {ex2:+.3f}, ${g.pnl_adj.sum():+.2f}, accts {sorted(g.acct.unique())}")
    if since:
        x = g[g.date >= since]
        out.append(f"   since {since}: {len(x)} trades, {x.rc.sum():+.2f}R, avg {x.rc.mean() if len(x) else float('nan'):+.3f}, ${x.pnl_adj.sum():+.2f}, win {(x.pnl > 0).mean() if len(x) else float('nan'):.0%}")
    out.append("   " + d.round(2).tail(8).to_string().replace("\n", "\n   "))
txt = "\n".join(out)
open(OUT / "onebig_out.txt", "w").write(txt + "\n\nEducational only - not financial advice.\n"); print(txt)
