"""Daily bars (Alpaca market-data GET only) for every symbol traded long since 10-23, to compute each stock's gap,
prior-day move, ATR%. Usage: python daily_fetch.py <scratch>. Educational only - not financial advice."""
import sys
from datetime import datetime
import pandas as pd
from alpaca.data.enums import Adjustment, DataFeed
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from mcf.data.alpaca_data import _client
S = sys.argv[1]
t = pd.read_parquet(f"{S}/trades.parquet")
syms = sorted(set(t.symbol) | {"SPY", "QQQ", "IWM"})
c = _client(); out = []
for i in range(0, len(syms), 200):
    req = StockBarsRequest(symbol_or_symbols=syms[i:i + 200], timeframe=TimeFrame.Day, start=datetime(2026, 9, 20),
                           end=datetime(2026, 11, 28), adjustment=Adjustment.SPLIT, feed=DataFeed("sip"))
    df = c.get_stock_bars(req).df.reset_index(); out.append(df); print(i, len(df), flush=True)
d = pd.concat(out); d["date"] = pd.to_datetime(d.timestamp).dt.tz_convert("America/New_York").dt.strftime("%Y-%m-%d")
d[["symbol", "date", "open", "high", "low", "close", "volume"]].to_parquet(f"{S}/daily.parquet"); print(len(d))
