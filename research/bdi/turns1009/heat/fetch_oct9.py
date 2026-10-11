"""Read-only SIP 1-minute bars (Alpaca market DATA client only; never trading endpoints) for the heat case study:
AAPL, SPCX, CAT, TSLA plus SPY/QQQ, 2026-09-21..2026-10-09 RTH -> data/oct9_1m.parquet.
Educational only - not financial advice."""
import os
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from alpaca.data.enums import Adjustment, DataFeed
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit

OUT = Path(__file__).resolve().parent / "data"
OUT.mkdir(exist_ok=True)
SYMS = ["AAPL", "SPCX", "CAT", "TSLA", "SPY", "QQQ"]

if __name__ == "__main__":
    cl = StockHistoricalDataClient(os.environ["ALPACA_API_KEY"], os.environ["ALPACA_SECRET_KEY"])
    req = StockBarsRequest(symbol_or_symbols=SYMS, timeframe=TimeFrame(1, TimeFrameUnit.Minute),
                           start=datetime(2026, 9, 21, 13, tzinfo=timezone.utc), end=datetime(2026, 10, 9, 20, 5, tzinfo=timezone.utc),
                           adjustment=Adjustment.SPLIT, feed=DataFeed("sip"))
    df = cl.get_stock_bars(req).df.reset_index()
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True).dt.tz_convert("America/New_York")
    t = df["timestamp"].dt.hour * 60 + df["timestamp"].dt.minute
    df = df[(t >= 570) & (t < 960)]
    df[["symbol", "timestamp", "open", "high", "low", "close", "volume"]].to_parquet(OUT / "oct9_1m.parquet", index=False)
    print(df.groupby("symbol").size())
