import sys, sqlite3
from datetime import datetime, timezone
from pathlib import Path
sys.path.insert(0, "/home/user/MCF")
from mcf.data.alpaca_data import _client, fetch_bars
S = Path(sys.argv[1]); syms = set()
for a in ("t1", "t2", "p"):
    c = sqlite3.connect(S / a / "journal.db")
    syms |= {r[0] for r in c.execute("select distinct symbol from orders where created_at like '2026-10-12%'")}
syms = sorted(s for s in syms if not (S / "bars" / f"{s}.parquet").exists())
print(syms)
if syms:
    for s, g in fetch_bars(syms, datetime(2026, 10, 12, 8, tzinfo=timezone.utc), datetime(2026, 10, 12, 21, tzinfo=timezone.utc), feed="sip", client=_client()).items():
        g.to_parquet(S / "bars" / f"{s}.parquet")
