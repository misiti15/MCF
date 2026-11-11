"""REGSW: 1-minute SIP bars for live days after the cache (11-05..) - SPY/QQQ/IWM/XLK/XLP/XLU/VXX + the 200 compass
names (breadth). Read-only market-data GET (the one compass_live uses). Usage: python fetch_live.py <scratch> [days...]
-> <scratch>/live_bars.parquet. Educational only - not financial advice."""
import sys
from pathlib import Path
import pandas as pd
sys.path.insert(0, "/home/user/MCF")
from mcf.report import compass_live as CL  # noqa: E402

S = Path(sys.argv[1]); NY = "America/New_York"
DAYS = sys.argv[2:] or ["2026-11-05", "2026-11-06", "2026-11-09", "2026-11-10"]
ETF = ["SPY", "QQQ", "IWM", "XLK", "XLP", "XLU", "VXX"]
names = CL.universe(); syms = list(dict.fromkeys(ETF + names))
out = []
for d in DAYS:
    bars = CL.fetch(d, syms, pd.Timestamp(f"{d} 16:00", tz=NY), log=lambda *a: None)
    for s, b in bars.items():
        b = b.copy(); b["symbol"] = s; b["date"] = d; b["hunch"] = s in names; out.append(b)
    print(d, len(bars), flush=True)
pd.concat(out).to_parquet(S / "live_bars.parquet")
