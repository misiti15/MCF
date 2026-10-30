"""Same-poll bursts: entries of ONE setup in ONE 5-min poll (cluster size), all accounts, real trades run 1,
10-06..10-30, costs in (R = pnl_adj / $ risk). Per account and for Gen: avg R by cluster size, share of days,
and the worst bursts. Also today's side split per account. Usage: python burst.py <scratch>
Educational only - not financial advice."""
import sys, sqlite3
from pathlib import Path
import numpy as np, pandas as pd
S = Path(sys.argv[1]); OUT = Path(__file__).resolve().parent; TZ = "America/New_York"
rows = []
for a in ("p", "t1", "t2", "gy", "gen"):
    c = sqlite3.connect(S / a / "journal.db")
    t = pd.read_sql("select date, strategy, symbol, side, signal_time, entry, stop, shares, pnl, pnl_adj, r_multiple from trades where run_id=1 and exit is not null", c)
    t["acct"] = a; rows.append(t)
T = pd.concat(rows, ignore_index=True); T["pnl_adj"] = T.pnl_adj.fillna(T.pnl)
T["risk"] = (T.entry - T.stop).abs() * T.shares; T["rc"] = np.where(T.risk > 0, T.pnl_adj / T.risk, T.r_multiple)
T["poll"] = pd.to_datetime(T.signal_time, utc=True, format="mixed").dt.tz_convert(TZ).dt.floor("5min")
T["cl"] = T.groupby(["acct", "date", "strategy", "poll"]).rc.transform("size")
T["clb"] = pd.cut(T.cl, [0, 1, 4, 9, 19, 999], labels=["1", "2-4", "5-9", "10-19", "20+"])
out = []
P = lambda *x: out.append(" ".join(str(y) for y in x))
P("== avg R after costs by same-setup same-poll cluster size (all sessions 10-06..10-30)")
P(T.pivot_table(index="acct", columns="clb", values="rc", aggfunc=["size", "mean"], observed=False).round(3).to_string())
B = T[T.cl >= 10].groupby(["acct", "date", "strategy", "poll"]).agg(n=("rc", "size"), R=("rc", "sum"), avg=("rc", "mean"), usd=("pnl_adj", "sum"), side=("side", "first")).reset_index()
P("\n== bursts of >= 10 entries:", len(B), "bursts,", int(B.n.sum()), "trades, sum", round(B.R.sum(), 1), "R, avg", round(B.R.sum() / B.n.sum(), 3),
  "| win bursts (R>0)", int((B.R > 0).sum()), "| best burst share of +R:", round(B.R.clip(lower=0).max() / max(B.R.clip(lower=0).sum(), 1e-9), 2))
P("by account:", B.groupby("acct").agg(bursts=("n", "size"), trades=("n", "sum"), R=("R", "sum"), usd=("usd", "sum")).round(1).to_dict("index"))
P("by side:", B.groupby("side").agg(bursts=("n", "size"), trades=("n", "sum"), R=("R", "sum")).round(1).to_dict("index"))
P("by day (sum R):", B.groupby("date").R.sum().round(1).to_dict())
P("worst 8:"); P(B.nsmallest(8, "R").assign(poll=lambda d: d.poll.dt.strftime("%H:%M")).to_string(index=False))
P("best 5:"); P(B.nlargest(5, "R").assign(poll=lambda d: d.poll.dt.strftime("%H:%M")).to_string(index=False))
x = B[B.date != "2026-10-30"]
P("w/o 10-30:", len(x), "bursts,", int(x.n.sum()), "trades, avg", round(x.R.sum() / max(x.n.sum(), 1), 3))
td = T[T.date == "2026-10-30"]
P("\n== 10-30 side split (R, $):", td.groupby(["acct", "side"]).agg(n=("rc", "size"), R=("rc", "sum"), usd=("pnl_adj", "sum")).round(1).to_dict("index"))
open(OUT / "burst_out.txt", "w").write("\n".join(out) + "\n\nEducational only - not financial advice.\n"); print("\n".join(out))
