"""E) Same-symbol re-entry after a stop-out (any setup, same account, same side, same day): live R of entries that
come after an earlier trade on that symbol + side was stopped out (exit before the new entry), vs all other entries.
All accounts, real trades, 10-06..10-27, costs in. Usage: python cooldown.py <scratch>   Educational only - not financial advice."""
import sys, sqlite3
from pathlib import Path
import pandas as pd
S = Path(sys.argv[1]); OUT = Path(__file__).resolve().parent; TZ = "America/New_York"
rows = []
for a in ("p", "t1", "t2", "gy", "gen"):
    c = sqlite3.connect(S / a / "journal.db")
    t = pd.read_sql("select date, symbol, strategy, side, entry, stop, shares, pnl_adj, entry_time, exit_time, exit_reason "
                    "from trades where run_id=1 and date >= '2026-10-06' and exit is not null", c)
    t["acct"] = a; rows.append(t)
T = pd.concat(rows, ignore_index=True)
T["risk"] = (T.entry - T.stop).abs() * T.shares; T = T[T.risk > 0].copy(); T["R"] = T.pnl_adj / T.risk
T["nt"] = pd.to_datetime(T.entry_time, utc=True, format="mixed"); T["et"] = pd.to_datetime(T.exit_time, utc=True, format="mixed")
T = T.sort_values("nt").reset_index(drop=True)
after, mins, same = [], [], []
for k, g in T.groupby(["acct", "date", "symbol", "side"]):
    stops = g[g.exit_reason == "stop"]
    for i, r in g.iterrows():
        prev = stops[stops.et < r.nt]
        after.append((i, len(prev) > 0)); mins.append((i, (r.nt - prev.et.max()).total_seconds() / 60 if len(prev) else None))
        same.append((i, bool((prev.strategy == r.strategy).any()) if len(prev) else None))
T["after_stop"] = pd.Series(dict(after)); T["min_since"] = pd.Series(dict(mins)); T["same_setup"] = pd.Series(dict(same))
def s(d): return f"n {len(d)}, win {100 * (d.pnl_adj > 0).mean():.0f}%, avgR {d.R.mean():+.3f}, sumR {d.R.sum():+.1f}, ${d.pnl_adj.sum():+.0f}, days {d.date.nunique()}"
out = ["after an earlier stop on the same symbol+side: " + s(T[T.after_stop]), "all other entries: " + s(T[~T.after_stop])]
A = T[T.after_stop]
out += ["  same setup re-entry: " + s(A[A.same_setup == True]), "  different setup: " + s(A[A.same_setup == False])]
for lo, hi in [(0, 30), (30, 90), (90, 999)]:
    out.append(f"  {lo}-{hi} min after the stop: " + s(A[(A.min_since >= lo) & (A.min_since < hi)]))
out.append("  by account: " + str(A.groupby("acct").R.agg(["size", "mean", "sum"]).round(3).to_dict("index")))
out.append("  by date (sum R): " + str(A.groupby("date").R.sum().round(1).to_dict()))
out.append("  by side: " + str(A.groupby("side").R.agg(["size", "mean"]).round(3).to_dict("index")))
txt = "\n".join(out) + "\n\nEducational only - not financial advice.\n"
open(OUT / "cooldown_out.txt", "w").write(txt); print(txt)
