"""Read-only SIP 1-minute bars (Alpaca market data only): SPY/QQQ/IWM 2026-10-09..10-16 full sessions, and the lab
universe 09:30-10:31 for 2026-10-12..10-16 (breadth at 10:00/10:30). Educational only - not financial advice.
Usage: python fetch_week.py <out_dir>"""
import sys
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd
sys.path.insert(0, "/home/user/MCF")
from mcf.data.alpaca_data import _client, fetch_bars
O = Path(sys.argv[1]); O.mkdir(parents=True, exist_ok=True)
cl = _client()
idx = fetch_bars(["SPY", "QQQ", "IWM"], datetime(2026, 10, 9, 13, tzinfo=timezone.utc), datetime(2026, 10, 16, 21, tzinfo=timezone.utc), feed="sip", client=cl)
for s, g in idx.items():
    g.to_parquet(O / f"idx_{s}.parquet")
syms = [l.strip() for l in open("/home/user/MCF/research/lab_symbols.txt") if l.strip()]
parts = []
for d in (12, 13, 14, 15, 16):
    a, b = datetime(2026, 10, d, 13, 30, tzinfo=timezone.utc), datetime(2026, 10, d, 14, 31, tzinfo=timezone.utc)
    for i in range(0, len(syms), 200):
        for s, g in fetch_bars(syms[i:i + 200], a, b, feed="sip", client=cl).items():
            g = g.copy(); g["symbol"] = s; parts.append(g)
pd.concat(parts).to_parquet(O / "uni_open.parquet")
print(len(idx), len(parts))
