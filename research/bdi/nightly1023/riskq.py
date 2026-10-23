"""Live record by $-risk quartile (slot-capped sizing => $ risk ~ slot x stop % of price), Primary / Testing 1 / Testing 2,
all sessions in the journals. R after costs = pnl_adj / $ risk. Feeds backlog nightly-1023-wide-stop-pct-risk.
Usage: python riskq.py <scratch> > riskq_out.txt   Educational only - not financial advice."""
import sys, sqlite3
import numpy as np, pandas as pd
S = sys.argv[1]
for a in ("p", "t1", "t2"):
    T = pd.read_sql("select date, strategy, entry, stop, shares, pnl, pnl_adj, r_multiple from trades where run_id=1 and exit is not null",
                    sqlite3.connect(f"{S}/{a}/journal.db"))
    T["pnl_adj"] = T.pnl_adj.fillna(T.pnl); T["risk"] = (T.entry - T.stop).abs() * T.shares; T = T[T.risk > 0]
    T["rc"] = T.pnl_adj / T.risk; T["stop_pct"] = (T.entry - T.stop).abs() / T.entry * 100
    T["q"] = pd.qcut(T.risk, 4, labels=["q1", "q2", "q3", "q4"])
    g = T.groupby("q", observed=True).agg(n=("rc", "size"), risk_med=("risk", "median"), stop_pct_med=("stop_pct", "median"),
                                          avgR=("rc", "mean"), usd=("pnl_adj", "sum"), R=("rc", "sum")).round(3)
    print(f"== {a}: {len(T)} trades, ${T.pnl_adj.sum():.2f}, {T.rc.sum():.2f}R, median $risk {T.risk.median():.2f}"); print(g)
print("\nEducational only - not financial advice.")
