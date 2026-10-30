"""PDL-long demotion-watch evaluation, 2026-10-29. Reads journals at <scratch>/{p,t1,t2,gy,gen}/journal.db (nightly1029 fetch).
R after costs = pnl_adj / $ risk (same as nightly1029/combined.py). Usage: python evalpdl.py <scratch>
Educational only - not financial advice."""
import sys, sqlite3
from pathlib import Path
import numpy as np, pandas as pd
S = Path(sys.argv[1])
SET = ["CWT14-failbrk-pdl-p05-long", "CWT14-failbrk-pdl-p05-lowvol-long", "CWT14-failbrk-pdl-p10-long"]
rows = []
for a in ("p", "t1", "t2", "gy", "gen"):
    c = sqlite3.connect(S / a / "journal.db")
    t = pd.read_sql("select date, symbol, strategy, entry, stop, shares, pnl, pnl_adj, r_multiple from trades where run_id=1 and exit is not null", c)
    t["acct"] = a; rows.append(t)
T = pd.concat(rows, ignore_index=True); T = T[T.strategy.isin(SET)].copy()
T["pnl_adj"] = T.pnl_adj.fillna(T.pnl); T["risk"] = (T.entry - T.stop).abs() * T.shares
T["rc"] = np.where(T.risk > 0, T.pnl_adj / T.risk, T.r_multiple)
D = T.date.max()
def rec(g, lab):
    n = len(g); day = g.groupby("date").rc.sum(); k = len(day); tot = g.rc.sum()
    aw = g.rc[g.rc > 0].mean(); al = -g.rc[g.rc <= 0].mean()
    bd = day.idxmax(); bn = (g.date == bd).sum()
    tday = day.mean() / (day.std(ddof=1) / k ** .5) if k > 1 else np.nan
    return f"{lab}: n {n}, sess {k}, win {(g.pnl_adj>0).mean():.3f} vs BE {al/(aw+al):.3f}, avgR {g.rc.mean():+.3f}, t_day {tday:+.2f}, " \
           f"w/o best day {(tot-day.max())/(n-bn):+.3f} (best {bd} {day.max():+.1f}R, share {day.max()/tot if tot>0 else float('nan'):.2f}; total {tot:+.1f}R), $ {g.pnl_adj.sum():+.0f}"
out = []
for s in SET:
    g = T[T.strategy == s]; td = g[g.date == D]
    out.append(f"== {s} accts {sorted(g.acct.unique())}")
    out.append(f"today {D}: n {len(td)}, sum R {td.rc.sum():+.2f}, avgR {td.rc.mean():+.3f}, $ {td.pnl_adj.sum():+.2f}, win {(td.pnl_adj>0).mean():.2f}")
    out.append(rec(g, "full")); out.append(rec(g[g.date >= "2026-10-27"], "since 10-27"))
    day = g.groupby("date").agg(n=("rc", "size"), R=("rc", "sum"), avg=("rc", "mean"))
    out.append("per session: " + "; ".join(f"{d[5:]} {r.n}/{r.R:+.1f}" for d, r in day.iterrows()))
    h = day.index[: len(day) // 2]; out.append(f"avgR first half {g[g.date.isin(h)].rc.mean():+.3f}, second half {g[~g.date.isin(h)].rc.mean():+.3f}")
# overlap
sd = T.groupby(["date", "symbol"]).strategy.nunique()
out.append(f"\nsymbol-days {len(sd)}; traded by 2+ {(sd>=2).mean():.2f}; by all 3 {(sd==3).mean():.2f}")
for s in SET:
    m = T[T.strategy == s].groupby(["date", "symbol"]).size().index
    out.append(f"  {s}: its symbol-days shared with another {(sd.loc[m]>=2).mean():.2f}")
P = T.pivot_table(index="date", columns="strategy", values="rc", aggfunc="sum")[SET]
out.append("same-day R correlation:\n" + P.corr().round(2).to_string())
P2 = T[T.date >= "2026-10-27"].groupby("strategy").rc.sum()
txt = "\n".join(out); print(txt); open(Path(__file__).parent / "evalpdl_out.txt", "w").write(txt + "\n\nEducational only - not financial advice.\n")
