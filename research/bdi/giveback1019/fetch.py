"""Read-only SIP 1-min bars (Alpaca market data only) for every live session 2026-10-06..10-16, all three accounts'
traded symbols plus SPY/QQQ/IWM. Writes <scratch>/bars/<date>/<sym>.parquet. Educational only - not financial advice."""
import sys, sqlite3
from datetime import datetime, timezone, date
from pathlib import Path
sys.path.insert(0, "/home/user/MCF")
from mcf.data.alpaca_data import _client, fetch_bars
S = Path(sys.argv[1]); LAST = "2026-10-16"
need = {}
for a in ("p", "t1", "t2"):
    c = sqlite3.connect(S / a / "journal.db")
    for d, s in c.execute("select distinct date, symbol from trades where run_id=1 and date<=?", (LAST,)):
        need.setdefault(d, {"SPY", "QQQ", "IWM"}).add(s)
cl = _client()
for d, syms in sorted(need.items()):
    out = S / "bars" / d; out.mkdir(parents=True, exist_ok=True)
    syms = sorted(x for x in syms if not (out / f"{x}.parquet").exists())
    y, m, dd = map(int, d.split("-"))
    a, b = datetime(y, m, dd, 13, tzinfo=timezone.utc), datetime(y, m, dd, 20, 30, tzinfo=timezone.utc)
    n = 0
    for i in range(0, len(syms), 100):
        for s, g in fetch_bars(syms[i:i + 100], a, b, feed="sip", client=cl).items():
            g.to_parquet(out / f"{s}.parquet"); n += 1
    print(d, len(syms), n, flush=True)
