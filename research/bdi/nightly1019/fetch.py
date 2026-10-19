"""Read-only SIP 1-min bars (Alpaca market data only) for 2026-10-19: every symbol traded (run 1) by Primary (p),
Testing 1 (t1), Testing 2 (t2) and the Setup Generator account (gen), plus SPY/QQQ/IWM.
Usage: python fetch.py <scratch>   (expects <scratch>/<acct>/journal.db; writes <scratch>/bars/<sym>.parquet)
Educational only - not financial advice."""
import sys, sqlite3
from datetime import datetime, timezone
from pathlib import Path
sys.path.insert(0, "/home/user/MCF")
from mcf.data.alpaca_data import _client, fetch_bars
S = Path(sys.argv[1]); D = "2026-10-19"
syms = {"SPY", "QQQ", "IWM"}
for a in ("p", "t1", "t2", "gen"):
    c = sqlite3.connect(S / a / "journal.db")
    syms |= {r[0] for r in c.execute("select distinct symbol from trades where date=? and run_id=1", (D,))}
    # plus submitted signals with no trade row (Testing 1's final push failed; t1_missing.py replays them)
    syms |= {r[0] for r in c.execute("select distinct symbol from signals where day=? and run_id=1 and status='submitted'", (D,))}
syms = sorted(x for x in syms if not (S / "bars" / f"{x}.parquet").exists()); (S / "bars").mkdir(exist_ok=True)
cl = _client()
a, b = datetime(2026, 10, 19, 13, tzinfo=timezone.utc), datetime(2026, 10, 19, 20, 30, tzinfo=timezone.utc)
n = 0
for i in range(0, len(syms), 100):
    for s, g in fetch_bars(syms[i:i + 100], a, b, feed="sip", client=cl).items():
        g.to_parquet(S / "bars" / f"{s}.parquet"); n += 1
print(len(syms), "symbols,", n, "with bars")
