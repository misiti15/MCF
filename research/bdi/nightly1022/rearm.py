"""Per-setup -2R daily stop: how often did a setup RE-ARM (a winner closing after the trip lifted realized R back above
-2R, so mcf/execution/risk.py let new entries through) and what did those post-trip entries do? Sessions 10-20..10-22
(stop live from 10-20) in the accounts that run it (Testing 1, Testing 2, Graveyard). Realized R = journal r_multiple
summed by exit time (what risk.py tracks); entry R after costs = pnl_adj / $ risk. Writes rearm_out.txt.
Usage: python rearm.py <scratch>   Educational only - not financial advice."""
import sys, sqlite3
from pathlib import Path
import numpy as np, pandas as pd
S = Path(sys.argv[1]); OUT = Path(__file__).resolve().parent; LIM = 2.0
rows = []
for a in ("t1", "t2", "gy"):
    c = sqlite3.connect(S / a / "journal.db")
    t = pd.read_sql("select date, strategy, symbol, entry, stop, shares, pnl_adj, r_multiple, entry_time, exit_time from trades "
                    "where run_id=1 and date >= '2026-10-20' and exit is not null", c)
    t["nt"] = pd.to_datetime(t.entry_time, utc=True, format="mixed"); t["et"] = pd.to_datetime(t.exit_time, utc=True, format="mixed")
    t["rc"] = t.pnl_adj / ((t.entry - t.stop).abs() * t.shares)
    for (d, s), g in t.groupby(["date", "strategy"]):
        ex = g.sort_values("et"); cum = ex.r_multiple.cumsum().values
        trip = np.argmax(cum <= -LIM) if (cum <= -LIM).any() else None
        if trip is None:
            continue
        t0 = ex.et.iloc[trip]
        after = g[g.nt > t0]
        if after.empty:
            continue
        rows.append(dict(acct=a, date=d, setup=s, trip=t0.tz_convert("America/New_York").strftime("%H:%M"),
                         n_after=len(after), R_after=round(after.rc.sum(), 2), day_R=round(g.rc.sum(), 2),
                         R_until_trip_entries=round(g[g.nt <= t0].rc.sum(), 2)))
R = pd.DataFrame(rows).sort_values(["date", "R_after"])
pd.set_option("display.width", 250)
tot = R.groupby("date").agg(events=("setup", "size"), n_after=("n_after", "sum"), R_after=("R_after", "sum")).round(2)
txt = R.to_string(index=False) + "\n\nby date:\n" + tot.to_string() + f"\n\nall: {len(R)} re-arm events, {int(R.n_after.sum())} entries after the trip, {R.R_after.sum():+.2f}R after costs"
open(OUT / "rearm_out.txt", "w").write(txt + "\n\nEducational only - not financial advice.\n")
print(txt)
