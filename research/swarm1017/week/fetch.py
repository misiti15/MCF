"""Read-only SIP 1-min bars (Alpaca market data only) for every traded symbol-day 2026-10-06..16 (+SPY/QQQ/IWM).
Usage: python fetch.py <scratch>. Educational only - not financial advice."""
import sys, sqlite3
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd
sys.path.insert(0, "/home/user/MCF")
from mcf.data.alpaca_data import _client, fetch_bars
S = Path(sys.argv[1]); (S / "bars").mkdir(exist_ok=True)
need = {}
for a in ("p", "t1", "t2"):
    c = sqlite3.connect(S / a / "journal.db")
    for d, s in c.execute("select distinct date, symbol from trades where run_id=1"):
        need.setdefault(d, set()).add(s)
cl = _client()
for d in sorted(need):
    out = S / "bars" / f"{d}.parquet"
    if out.exists(): continue
    syms = sorted(need[d] | {"SPY", "QQQ", "IWM"})
    y, m, dd = map(int, d.split("-"))
    a, b = datetime(y, m, dd, 13, tzinfo=timezone.utc), datetime(y, m, dd, 20, 30, tzinfo=timezone.utc)
    parts = []
    for i in range(0, len(syms), 100):
        for s, g in fetch_bars(syms[i:i + 100], a, b, feed="sip", client=cl).items():
            g = g[["open", "high", "low", "close", "volume"]].copy(); g["symbol"] = s; parts.append(g)
    df = pd.concat(parts); df.index.name = "ts"; df.reset_index().to_parquet(out)
    print(d, len(syms), len(df), flush=True)
