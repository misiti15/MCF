"""Whole-universe scan from Alpaca snapshots (latest trade, quote, minute bar, daily bar, prev day).

100 symbols per request -> ~35 requests per pass over 3,500 symbols, well inside the free plan's
200 requests/min, so the entire universe can be re-ranked every minute at $0 (MarcoFlow needed
several 40-second heartbeats to cover its universe once, on 15-min-delayed bars).

On the free plan the feed is IEX: prices track the consolidated tape closely, volume does not
(~2-3% share). So the free scanner ranks on PRICE-based fields plus *IEX-relative* volume
(today's IEX volume vs that symbol's own typical IEX volume), which cancels IEX's share as long as
it is stable per symbol. `scripts/validate_iex_proxy.py` measures how well that proxy matches SIP
relative volume before we rely on it. With the $99 SIP plan the same code runs on feed="sip".
"""

from __future__ import annotations

import os

import numpy as np
import pandas as pd


def snapshots(symbols: list[str], feed: str = "iex", client=None, batch: int = 100) -> pd.DataFrame:
    from alpaca.data.enums import DataFeed
    from alpaca.data.historical import StockHistoricalDataClient
    from alpaca.data.requests import StockSnapshotRequest

    client = client or StockHistoricalDataClient(os.environ["ALPACA_API_KEY"], os.environ["ALPACA_SECRET_KEY"])
    rows = []
    for i in range(0, len(symbols), batch):
        snap = client.get_stock_snapshot(StockSnapshotRequest(symbol_or_symbols=symbols[i:i + batch], feed=DataFeed(feed)))
        for sym, s in snap.items():
            d, p, m, q, tr = s.daily_bar, s.previous_daily_bar, s.minute_bar, s.latest_quote, s.latest_trade
            if not (d and p and tr):
                continue
            bid, ask = (q.bid_price, q.ask_price) if q else (np.nan, np.nan)
            rows.append({
                "symbol": sym, "last": tr.price, "last_time": tr.timestamp,
                "open": d.open, "high": d.high, "low": d.low, "volume_today": d.volume,
                "prev_close": p.close, "prev_volume": p.volume,
                "min_close": m.close if m else np.nan, "min_volume": m.volume if m else np.nan,
                "bid": bid, "ask": ask,
            })
    return pd.DataFrame(rows)


def rank(snap: pd.DataFrame, universe: pd.DataFrame, minutes_since_open: int) -> pd.DataFrame:
    """Add scan features and an 'in play' score. Purely price/range based plus IEX-relative volume."""
    df = snap.merge(universe[["symbol", "adv", "avg_volume", "atr", "shortable", "easy_to_borrow"]], on="symbol", how="left")
    df["gap_pct"] = (df["open"] / df["prev_close"] - 1) * 100
    df["chg_pct"] = (df["last"] / df["prev_close"] - 1) * 100
    df["from_open_pct"] = (df["last"] / df["open"] - 1) * 100
    df["range_atr"] = (df["high"] - df["low"]) / df["atr"]
    mid = (df["bid"] + df["ask"]) / 2
    df["spread_bps"] = np.where(mid > 0, (df["ask"] - df["bid"]) / mid * 1e4, np.nan)
    # volume pace vs yesterday (same feed on both sides, so the IEX share cancels)
    frac = min(max(minutes_since_open, 1), 390) / 390
    df["vol_pace"] = df["volume_today"] / (df["prev_volume"] * frac).replace(0, np.nan)
    df["in_play"] = (df["range_atr"].rank(pct=True) + df["vol_pace"].rank(pct=True) + df["gap_pct"].abs().rank(pct=True)) / 3
    return df.sort_values("in_play", ascending=False)
