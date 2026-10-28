"""F) NS3-family failed-VWAP-reclaim shorts (NS3-*, NS3V1-*, RW4-ns3-*; all accounts, real trades, 10-06..10-28, costs in):
(1) by the n-th NS3-family short on the same symbol that day in that account; (2) entries after an earlier NS3-family stop
on that symbol today vs first touch; (3) the crypto-miner / AI-power names (fixed list below, picked AFTER seeing 10-28,
so (3) is descriptive only) vs the rest; (4) per day. Usage: python ns3fam.py <scratch>   Educational only - not financial advice."""
import sys, sqlite3
from pathlib import Path
import pandas as pd
S = Path(sys.argv[1]); OUT = Path(__file__).resolve().parent
MINERS = {"CORZ", "WULF", "IREN", "CLSK", "HUT", "APLD", "CIFR", "RIOT", "MARA", "BTDR", "BITF", "GLXY", "SEI", "NBIS", "OKLO"}
rows = []
for a in ("p", "t1", "t2", "gy", "gen"):
    c = sqlite3.connect(S / a / "journal.db")
    t = pd.read_sql("select date, symbol, strategy, side, entry, stop, shares, pnl_adj, entry_time, exit_time, exit_reason "
                    "from trades where run_id=1 and date >= '2026-10-06' and exit is not null and side=-1 "
                    "and (strategy like 'NS3%' or strategy like 'RW4-ns3%')", c)
    t["acct"] = a; rows.append(t)
T = pd.concat(rows, ignore_index=True)
T["risk"] = (T.entry - T.stop).abs() * T.shares; T = T[T.risk > 0].copy(); T["R"] = T.pnl_adj / T.risk
T["nt"] = pd.to_datetime(T.entry_time, utc=True, format="mixed"); T["et"] = pd.to_datetime(T.exit_time, utc=True, format="mixed")
T = T.sort_values("nt").reset_index(drop=True)
T["nth"] = T.groupby(["acct", "date", "symbol"]).cumcount() + 1
T["after_stop"] = [bool(((T.acct == r.acct) & (T.date == r.date) & (T.symbol == r.symbol) & (T.exit_reason == "stop") & (T.et < r.nt)).any())
                   for r in T.itertuples()]
T["miner"] = T.symbol.isin(MINERS)
def s(d):
    if not len(d): return "n 0"
    g = d.groupby("date").R.sum()
    return (f"n {len(d)}, win {100 * (d.pnl_adj > 0).mean():.0f}%, avgR {d.R.mean():+.3f}, sumR {d.R.sum():+.1f}, ${d.pnl_adj.sum():+.0f}, "
            f"days {d.date.nunique()}, best day {g.idxmax()} {g.max():+.1f}R, w/o 10-28 avgR {d[d.date != '2026-10-28'].R.mean():+.3f}")
out = ["== NS3 family shorts, all: " + s(T)]
for k in (1, 2, 3): out.append(f"  {k}{'+' if k == 3 else ''}-th on the symbol that day: " + s(T[T.nth >= 3] if k == 3 else T[T.nth == k]))
out += ["  after an earlier NS3-family stop on the symbol today: " + s(T[T.after_stop]), "  no earlier stop: " + s(T[~T.after_stop])]
out += ["  miner / AI-power list: " + s(T[T.miner]), "  other names: " + s(T[~T.miner])]
out.append("  by setup: " + str(T.groupby("strategy").R.agg(["size", "mean", "sum"]).round(3).to_dict("index")))
out.append("  by date (sum R): " + str(T.groupby("date").R.sum().round(1).to_dict()))
txt = "\n".join(out); open(OUT / "ns3fam_out.txt", "w").write(txt + "\n\nEducational only - not financial advice.\n"); print(txt)
