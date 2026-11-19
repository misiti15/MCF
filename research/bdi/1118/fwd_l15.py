"""swing1118-L15 forward shadow (journal-only): live short lots still open at 15:30 in names <= -2% from the open, closed at the
15:30 close (1c + 1 bp per side, both sides) vs their actual exit. Usage: python fwd_l15.py <scratch> <day>; <scratch>/<acct>/journal.db
(p testing testing2 explore1 livelab testingd testinge testingf gen graveyard) + <scratch>/bars/<SYM>.parquet (1-min SIP).
Educational only - not financial advice."""
import sqlite3, sys
from pathlib import Path
import numpy as np, pandas as pd
S = Path(sys.argv[1]); D = sys.argv[2]; TZ = "America/New_York"
NAMES = dict(p="Primary", testing="On Deck", testing2="Testing A", explore1="Testing B", livelab="Testing C", testingd="Testing D",
             testinge="Testing E", testingf="Testing F", gen="Gen", graveyard="Graveyard")
t1530 = pd.Timestamp(f"{D} 15:30", tz=TZ); cache = {}
def px(s):
    if s not in cache:
        b = pd.read_parquet(S / "bars" / f"{s}.parquet"); b.index = pd.to_datetime(b.index, utc=True).tz_convert(TZ)
        cache[s] = (b.open.iloc[0], b.close[b.index < t1530].iloc[-1])
    return cache[s]
tot = []
for a, nm in NAMES.items():
    t = pd.read_sql("select symbol,strategy,side,entry_time,exit_time,entry,stop,shares,pnl_adj from trades where date=? and run_id=1 and side=-1",
                    sqlite3.connect(S / a / "journal.db"), params=(D,))
    for k in ("entry_time", "exit_time"): t[k] = pd.to_datetime(t[k], utc=True, format="mixed").dt.tz_convert(TZ)
    t = t[(t.entry_time < t1530) & (t.exit_time > t1530)].copy()
    if t.empty: tot.append((nm, 0, 0, 0.0, 0)); continue
    t["risk"] = (t.entry - t.stop).abs() * t.shares; t["R"] = t.pnl_adj / t.risk
    oc = t.symbol.map(px); t["o"] = [x[0] for x in oc]; t["c"] = [x[1] for x in oc]
    t["fo"] = (t.c / t.o - 1) * 100
    t["alt"] = (t.entry - t.c) * t.shares / t.risk - 2 * (0.01 + t.entry * 1e-4) * t.shares / t.risk
    L = t[t.fo <= -2.0]
    tot.append((nm, len(t), len(L), float((L.alt - L.R).sum()), int(((L.alt - L.R) > 0).sum())))
for r in tot: print(f"{r[0]}: short lots open at 15:30 {r[1]}, in -2% losers {r[2]}, delta {r[3]:+.2f}R, better {r[4]}")
print("all accounts delta %+.2fR on %d lots" % (sum(r[3] for r in tot), sum(r[2] for r in tot)))
