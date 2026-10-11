"""Read-only SIP 1-minute bars (Alpaca market DATA only, never trading endpoints) for the 2026-10-09 turn case studies.
(1) focus + context symbols, 2026-09-02..2026-10-09, 04:00-20:00 ET (extended hours kept) -> data/focus_1m.parquet
(2) lab universe (research/lab_symbols.txt), 2026-10-09 regular session only -> data/universe_1009.parquet
Educational only - not financial advice."""
import os
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from alpaca.data.enums import Adjustment, DataFeed
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OUT = HERE / "data"
OUT.mkdir(exist_ok=True)
cl = StockHistoricalDataClient(os.environ["ALPACA_API_KEY"], os.environ["ALPACA_SECRET_KEY"])
FOCUS = ["AAPL", "SPCX", "CAT", "TSLA", "SPY", "QQQ", "XLK", "XLI", "XLY", "IWM"]


def get(syms, a, b):
    req = StockBarsRequest(symbol_or_symbols=syms, timeframe=TimeFrame(1, TimeFrameUnit.Minute), start=a, end=b,
                           adjustment=Adjustment.SPLIT, feed=DataFeed("sip"))
    df = cl.get_stock_bars(req).df
    if df.empty:
        return df
    df = df.reset_index()
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True).dt.tz_convert("America/New_York")
    return df[["symbol", "timestamp", "open", "high", "low", "close", "volume", "trade_count", "vwap"]]


if __name__ == "__main__":
    a, b = datetime(2026, 9, 2, 8, tzinfo=timezone.utc), datetime(2026, 10, 10, 0, tzinfo=timezone.utc)
    F = get(FOCUS, a, b)
    F.to_parquet(OUT / "focus_1m.parquet")
    print("focus", F.symbol.nunique(), len(F), F.timestamp.min(), F.timestamp.max())
    uni = [s.strip() for s in (ROOT / "research" / "lab_symbols.txt").read_text().split() if s.strip()]
    a1, b1 = datetime(2026, 10, 9, 13, 30, tzinfo=timezone.utc), datetime(2026, 10, 9, 20, 0, tzinfo=timezone.utc)
    parts = []
    for i in range(0, len(uni), 100):
        parts.append(get(uni[i:i + 100], a1, b1))
    U = pd.concat(parts)
    U.to_parquet(OUT / "universe_1009.parquet")
    print("universe", U.symbol.nunique(), len(U))


def fetch_universe_1008():
    """10-08 regular session for the lab universe (the bar cache ends 10-07), so breadth has 20 full prior sessions."""
    uni = [s.strip() for s in (ROOT / "research" / "lab_symbols.txt").read_text().split() if s.strip()]
    a1, b1 = datetime(2026, 10, 8, 13, 30, tzinfo=timezone.utc), datetime(2026, 10, 8, 20, 0, tzinfo=timezone.utc)
    U = pd.concat([get(uni[i:i + 100], a1, b1) for i in range(0, len(uni), 100)])
    U.to_parquet(OUT / "universe_1008.parquet")
    print("universe 10-08", U.symbol.nunique(), len(U))
