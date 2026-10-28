"""hf1027: read-only SIP 1-min bars (Alpaca market data only), 09:30-16:00 ET, for every symbol-day traded by the
24 HF setups (hf_setups.csv) 2026-10-09..10-27. Writes <scratch>/bars/<date>/<sym>.parquet.
Usage: python fetch.py <scratch>   Educational only - not financial advice."""
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
import pandas as pd
sys.path.insert(0, "/home/user/MCF")
from mcf.data.alpaca_data import _client, fetch_bars
S = Path(sys.argv[1]); HERE = Path(__file__).resolve().parent; ET = ZoneInfo("America/New_York")
T = pd.read_parquet(S / "all_trades.parquet"); T = T[(T.date >= "2026-10-09") & T.strategy.isin(pd.read_csv(HERE / "hf_setups.csv").setup)]
cl = _client(); n = 0
for d, g in T.groupby("date"):
    o = S / "bars" / d; o.mkdir(parents=True, exist_ok=True)
    syms = sorted(x for x in g.symbol.unique() if not (o / f"{x}.parquet").exists())
    y, m, dd = map(int, d.split("-"))
    a, b = datetime(y, m, dd, 9, 30, tzinfo=ET), datetime(y, m, dd, 16, 0, tzinfo=ET)
    for i in range(0, len(syms), 100):
        for s, b_ in fetch_bars(syms[i:i + 100], a, b, feed="sip", client=cl).items():
            b_.to_parquet(o / f"{s}.parquet"); n += 1
    print(d, len(syms), flush=True)
print(n, "symbol-days with bars")
