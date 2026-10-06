"""Tradable universe: ~3,500 liquid US stocks/ETFs, rebuilt daily before the open.

MarcoFlow lesson: its universe was curated by hand + an IEX-volume ADV screen, and IEX volume
understates the tape ~30-40x. MCF ranks by *consolidated* average dollar volume from SIP daily
bars (free on Alpaca when >15 min old), so liquidity numbers are real.

Filters (config `universe`): price >= min_price, ATR >= min_atr_pct of price (drops T-bill/money-market
ETFs that cannot move enough to beat costs), active & tradable, major exchange, common stock or ETF
(no warrants/units/rights/preferreds). Two tiers, no fixed count:
  core      20d ADV >= min_avg_dollar_volume           tradable every day
  extended  20d ADV >= extended_min_avg_dollar_volume  tradable only on days it is in play
            (opening rvol >= extended_min_rvol), at extended_slippage_per_share costs
`max_symbols` (null = no cap) only trims by ADV if set. Records shortable / easy_to_borrow.
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

import numpy as np
import pandas as pd

EXCHANGES = {"NYSE", "NASDAQ", "ARCA", "AMEX", "BATS"}
BAD_SUFFIX = ("W", "WS", "U", "R")  # warrants, units, rights (5-letter Nasdaq suffixes)


def _clients():
    from alpaca.data.historical import StockHistoricalDataClient
    from alpaca.trading.client import TradingClient

    k, s = os.environ["ALPACA_API_KEY"], os.environ["ALPACA_SECRET_KEY"]
    return TradingClient(k, s, paper=True), StockHistoricalDataClient(k, s)


def candidate_assets(tc) -> pd.DataFrame:
    from alpaca.trading.enums import AssetClass, AssetStatus
    from alpaca.trading.requests import GetAssetsRequest

    rows = []
    for a in tc.get_all_assets(GetAssetsRequest(status=AssetStatus.ACTIVE, asset_class=AssetClass.US_EQUITY)):
        ex = str(getattr(a.exchange, "value", a.exchange))
        sym = a.symbol
        if not a.tradable or ex not in EXCHANGES or "." in sym or "/" in sym:
            continue
        if len(sym) == 5 and sym.endswith(BAD_SUFFIX):
            continue
        rows.append({"symbol": sym, "name": a.name, "exchange": ex, "shortable": bool(a.shortable),
                     "easy_to_borrow": bool(a.easy_to_borrow), "marginable": bool(a.marginable)})
    return pd.DataFrame(rows)


def daily_stats(dc, symbols: list[str], days: int = 30, batch: int = 200) -> pd.DataFrame:
    from alpaca.data.enums import Adjustment, DataFeed
    from alpaca.data.requests import StockBarsRequest
    from alpaca.data.timeframe import TimeFrame

    end = datetime.now(timezone.utc) - timedelta(minutes=20)  # free plan: SIP must be >15 min old
    start = end - timedelta(days=days * 1.6)
    out = []
    for i in range(0, len(symbols), batch):
        req = StockBarsRequest(symbol_or_symbols=symbols[i:i + batch], timeframe=TimeFrame.Day, start=start,
                               end=end, adjustment=Adjustment.SPLIT, feed=DataFeed.SIP)
        df = dc.get_stock_bars(req).df
        if df.empty:
            continue
        for sym, g in df.groupby(level=0):
            g = g.tail(20)
            pc = g["close"].shift()
            tr = pd.concat([g["high"] - g["low"], (g["high"] - pc).abs(), (g["low"] - pc).abs()], axis=1).max(axis=1)
            out.append({"symbol": sym, "price": float(g["close"].iloc[-1]),
                        "adv": float((g["close"] * g["volume"]).mean()),
                        "avg_volume": float(g["volume"].mean()),
                        "atr": float(tr.tail(14).mean()), "days": len(g)})
    st = pd.DataFrame(out)
    if not st.empty:
        st["atr_pct"] = st["atr"] / st["price"] * 100
    return st


def build_universe(cfg: dict, out_path: str = "data/universe.csv") -> pd.DataFrame:
    u, c = cfg["universe"], cfg["costs"]
    tc, dc = _clients()
    assets = candidate_assets(tc)
    stats = daily_stats(dc, assets["symbol"].tolist())
    df = assets.merge(stats, on="symbol", how="inner")
    from ..backtest.engine import pinned_symbols

    floor = min(u.get("extended_min_avg_dollar_volume", u["min_avg_dollar_volume"]), u["min_avg_dollar_volume"])
    keep = ((df.price >= c["min_price"]) & (df.adv >= floor) & (df.days >= 15)
            & (df.atr_pct >= u.get("min_atr_pct", 0.0)))
    df = df[keep | df.symbol.isin(pinned_symbols(cfg))]
    df = df.sort_values("adv", ascending=False)
    if u.get("max_symbols"):
        df = df.head(u["max_symbols"])
    df = df.reset_index(drop=True)
    df["tier"] = np.where(df.adv >= u["min_avg_dollar_volume"], "core", "extended")
    df["adv_rank"] = np.arange(1, len(df) + 1)
    df["built_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    df.to_csv(out_path, index=False)
    return df


def load_universe(path: str = "data/universe.csv") -> pd.DataFrame:
    return pd.read_csv(path)
