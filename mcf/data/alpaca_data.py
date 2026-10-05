"""Historical bar download from Alpaca Market Data into the local BarStore."""

from __future__ import annotations

import os
from datetime import datetime

import pandas as pd

from .bars import normalize, rth
from .store import BarStore


def _client():
    from alpaca.data.historical import StockHistoricalDataClient

    return StockHistoricalDataClient(os.environ["ALPACA_API_KEY"], os.environ["ALPACA_SECRET_KEY"])


def fetch_bars(
    symbols: list[str],
    start: datetime,
    end: datetime,
    feed: str = "iex",
    minutes: int = 1,
    client=None,
) -> dict[str, pd.DataFrame]:
    from alpaca.data.enums import Adjustment, DataFeed
    from alpaca.data.requests import StockBarsRequest
    from alpaca.data.timeframe import TimeFrame, TimeFrameUnit

    client = client or _client()
    req = StockBarsRequest(
        symbol_or_symbols=symbols,
        timeframe=TimeFrame(minutes, TimeFrameUnit.Minute),
        start=start,
        end=end,
        adjustment=Adjustment.SPLIT,
        feed=DataFeed(feed),
    )
    df = client.get_stock_bars(req).df  # MultiIndex (symbol, timestamp)
    out: dict[str, pd.DataFrame] = {}
    if df.empty:
        return out
    for sym, g in df.groupby(level=0):
        out[sym] = rth(normalize(g.droplevel(0)))
    return out


def download_to_store(
    symbols: list[str], start: datetime, end: datetime, store: BarStore, feed="iex", batch=100
) -> int:
    """Download in symbol batches (the API pages internally). Returns symbols saved."""
    client = _client()
    saved = 0
    for i in range(0, len(symbols), batch):
        chunk = symbols[i : i + batch]
        for sym, df in fetch_bars(chunk, start, end, feed=feed, client=client).items():
            store.save(sym, df)
            saved += 1
    return saved


def tradable_universe(min_price: float = 5.0) -> list[str]:
    """All active, tradable US equities/ETFs on major exchanges (pre-filter; liquidity filter later)."""
    from alpaca.trading.client import TradingClient
    from alpaca.trading.enums import AssetClass, AssetStatus
    from alpaca.trading.requests import GetAssetsRequest

    tc = TradingClient(os.environ["ALPACA_API_KEY"], os.environ["ALPACA_SECRET_KEY"], paper=True)
    assets = tc.get_all_assets(GetAssetsRequest(status=AssetStatus.ACTIVE, asset_class=AssetClass.US_EQUITY))
    keep = {"NYSE", "NASDAQ", "ARCA", "AMEX", "BATS"}
    return sorted(
        a.symbol
        for a in assets
        if a.tradable and str(getattr(a.exchange, "value", a.exchange)) in keep and "." not in a.symbol
    )
