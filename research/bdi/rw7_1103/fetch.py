"""Read-only SIP 1-min bars (Alpaca market data GET only) for every symbol RW7-gapdn-bounce-early-short-FD traded live
(Testing 1, run 1), on its trade dates, plus SPY/QQQ/IWM every session 10-12..11-03.
Usage: python fetch.py <scratch>  (expects <scratch>/t1/journal.db; writes <scratch>/bars/<date>/<sym>.parquet)
Educational only - not financial advice."""
import sys, sqlite3
from datetime import datetime, timezone
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from mcf.data.alpaca_data import _client, fetch_bars
S = Path(sys.argv[1])
t = sqlite3.connect(S / "t1" / "journal.db").execute(
    "select date, symbol from trades where strategy='RW7-gapdn-bounce-early-short-FD' and run_id=1").fetchall()
need = {}
for d, s in t:
    need.setdefault(d, set()).add(s)
for d in need:
    need[d] |= {"SPY", "QQQ", "IWM"}
cl = _client()
for d, syms in sorted(need.items()):
    o = S / "bars" / d; o.mkdir(parents=True, exist_ok=True)
    syms = sorted(x for x in syms if not (o / f"{x}.parquet").exists())
    y, m, dd = map(int, d.split("-"))
    a, b = datetime(y, m, dd, 13, 25, tzinfo=timezone.utc), datetime(y, m, dd, 21, 5, tzinfo=timezone.utc)
    for i in range(0, len(syms), 100):
        for s, g in fetch_bars(syms[i:i + 100], a, b, feed="sip", client=cl).items():
            g.to_parquet(o / f"{s}.parquet")
    print(d, len(syms), flush=True)

# daily bars (gap, ATR%, ADV context) 2026-08-15..11-03, split-adjusted
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from alpaca.data.enums import DataFeed, Adjustment
allsyms = sorted(set().union(*need.values()))
out = []
for i in range(0, len(allsyms), 100):
    r = cl.get_stock_bars(StockBarsRequest(symbol_or_symbols=allsyms[i:i + 100], timeframe=TimeFrame.Day,
                          start=datetime(2026, 8, 15, tzinfo=timezone.utc), end=datetime(2026, 11, 4, tzinfo=timezone.utc),
                          feed=DataFeed.SIP, adjustment=Adjustment.SPLIT)).df
    out.append(r.reset_index())
import pandas as pd
pd.concat(out).to_parquet(S / "daily.parquet"); print("daily", len(allsyms))
