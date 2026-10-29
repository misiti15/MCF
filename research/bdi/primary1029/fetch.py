"""Read-only SIP 1-min bars (Alpaca market data only) for 2026-10-29: every symbol Primary signalled (submitted or
skipped) plus SPY/QQQ/IWM and the sector ETFs. Usage: python fetch.py <scratch> (expects <scratch>/p/journal.db;
writes <scratch>/bars/<sym>.parquet; re-run after the close with --force to refresh). Educational only - not financial advice."""
import sys, sqlite3
from datetime import datetime, timezone
from pathlib import Path
sys.path.insert(0, "/home/user/MCF")
from mcf.data.alpaca_data import _client, fetch_bars
S = Path(sys.argv[1]); D = "2026-10-29"; force = "--force" in sys.argv
syms = {"SPY", "QQQ", "IWM", "XLK", "IGV", "XLV", "XBI", "XLI", "XLY", "XLP", "XLF", "SMH"}
c = sqlite3.connect(S / "p" / "journal.db")
syms |= {r[0] for r in c.execute("select distinct symbol from signals where day=? and run_id=1", (D,))}
(S / "bars").mkdir(exist_ok=True)
syms = sorted(x for x in syms if force or not (S / "bars" / f"{x}.parquet").exists())
cl = _client()
a, b = datetime(2026, 10, 29, 13, tzinfo=timezone.utc), datetime(2026, 10, 29, 20, 30, tzinfo=timezone.utc)
n = 0
for i in range(0, len(syms), 100):
    for s, g in fetch_bars(syms[i:i + 100], a, b, feed="sip", client=cl).items():
        g.to_parquet(S / "bars" / f"{s}.parquet"); n += 1
print(len(syms), "symbols,", n, "with bars")
