"""Alpaca paper/live broker adapter. Orders are bracket orders so every position
has a resting stop on the broker side even if this process dies."""

from __future__ import annotations

import os

from ..strategies.base import Signal


class AlpacaBroker:
    def __init__(self, paper: bool = True):
        from alpaca.trading.client import TradingClient

        self.client = TradingClient(os.environ["ALPACA_API_KEY"], os.environ["ALPACA_SECRET_KEY"], paper=paper)

    def can_short(self, symbol: str) -> bool:
        """Shortable and easy-to-borrow per the broker (cached for the session)."""
        cache = self.__dict__.setdefault("_short_cache", {})
        if symbol not in cache:
            a = self.client.get_asset(symbol)
            cache[symbol] = bool(a.shortable and a.easy_to_borrow)
        return cache[symbol]

    def equity(self) -> float:
        return float(self.client.get_account().equity)

    def clock(self):
        return self.client.get_clock()

    def submit_bracket(self, sig: Signal, qty: int, client_order_id: str):
        from alpaca.trading.enums import OrderClass, OrderSide, TimeInForce
        from alpaca.trading.requests import MarketOrderRequest, StopLossRequest, TakeProfitRequest

        kw = dict(
            symbol=sig.symbol,
            qty=qty,
            side=OrderSide.BUY if sig.side == 1 else OrderSide.SELL,
            time_in_force=TimeInForce.DAY,
            client_order_id=client_order_id,
            stop_loss=StopLossRequest(stop_price=round(sig.stop, 2)),
        )
        if sig.target is not None:
            kw["order_class"] = OrderClass.BRACKET
            kw["take_profit"] = TakeProfitRequest(limit_price=round(sig.target, 2))
        else:
            kw["order_class"] = OrderClass.OTO
        return self.client.submit_order(MarketOrderRequest(**kw))

    def positions(self) -> dict[str, object]:
        return {p.symbol: p for p in self.client.get_all_positions()}

    def close_position(self, symbol: str):
        return self.client.close_position(symbol)

    def orders_today_with_prefix(self, prefix: str, after) -> list:
        """All of today's orders (any status, with bracket/OTO legs) whose client_order_id starts with prefix."""
        from alpaca.trading.enums import QueryOrderStatus
        from alpaca.trading.requests import GetOrdersRequest

        out = self.client.get_orders(GetOrdersRequest(status=QueryOrderStatus.ALL, after=after, nested=True, limit=500))
        return [o for o in out if (o.client_order_id or "").startswith(prefix)]

    def cancel_orders_with_prefix(self, prefix: str) -> int:
        """Cancel open orders whose client_order_id starts with `prefix` (this system's orders only)."""
        from alpaca.trading.enums import QueryOrderStatus
        from alpaca.trading.requests import GetOrdersRequest

        n = 0
        for o in self.client.get_orders(GetOrdersRequest(status=QueryOrderStatus.OPEN, nested=True, limit=500)):
            if (o.client_order_id or "").startswith(prefix):
                self.client.cancel_order_by_id(o.id)
                n += 1
        return n

    def flatten_all(self):
        self.client.cancel_orders()
        return self.client.close_all_positions(cancel_orders=True)

    def closed_orders_today(self, after):
        from alpaca.trading.enums import QueryOrderStatus
        from alpaca.trading.requests import GetOrdersRequest

        return self.client.get_orders(GetOrdersRequest(status=QueryOrderStatus.CLOSED, after=after, nested=True, limit=500))
