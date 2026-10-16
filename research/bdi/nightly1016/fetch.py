"""Read-only SIP 1-min bars (Alpaca market data only) for 2026-10-16 traded symbols. Educational only."""
import sys, sqlite3
from datetime import datetime, timezone
from pathlib import Path
sys.path.insert(0, "/home/user/MCF")
from mcf.data.alpaca_data import _client, fetch_bars
S = Path(sys.argv[1])
syms = set(["SPY", "QQQ", "IWM"])
for a in ("p", "t1", "t2"):
    c = sqlite3.connect(S / a / "journal.db")
    syms |= {r[0] for r in c.execute("select distinct symbol from trades where date='2026-10-16' and run_id=1")}
syms = sorted(syms)
cl = _client()
a, b = datetime(2026, 10, 16, 8, tzinfo=timezone.utc), datetime(2026, 10, 16, 21, tzinfo=timezone.utc)
n = 0
for i in range(0, len(syms), 100):
    for s, g in fetch_bars(syms[i:i + 100], a, b, feed="sip", client=cl).items():
        g.to_parquet(S / "bars" / f"{s}.parquet"); n += 1
print(len(syms), n)
