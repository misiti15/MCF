"""Alpaca paper/live broker adapter. Orders are bracket orders so every position
has a resting stop on the broker side even if this process dies."""

from __future__ import annotations

import os

from ..strategies.base import Signal


class AlpacaBroker:
    def __init__(self, paper: bool = True):
        from alpaca.trading.client import TradingClient

        # Orders go to ALPACA_TRADE_* when set (the Testing account); market data always uses ALPACA_API_KEY (SIP plan).
        k = os.environ.get("ALPACA_TRADE_API_KEY") or os.environ["ALPACA_API_KEY"]
        sec = os.environ.get("ALPACA_TRADE_SECRET_KEY") or os.environ["ALPACA_SECRET_KEY"]
        self.client = TradingClient(k, sec, paper=paper)

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

    def close_mcf_position(self, symbol: str, prefix: str, wait_s: float = 15.0, tries: int = 5, sleep=None) -> bool:
        """Cancel this system's open orders on `symbol`, wait until the broker has released the shares, then close.

        Bracket/OTO legs hold the position's shares; a close sent before the cancels settle is rejected with
        "insufficient qty available" (2026-10-06: all 10 closes at 15:55 failed this way). Returns True when the
        position is gone. Only this system's orders are touched (the account is shared)."""
        import time as _t

        sleep = sleep or _t.sleep
        for o in self._open_mcf(symbol, prefix):
            try:
                self.client.cancel_order_by_id(o.id)
            except Exception as e:                       # already filled/cancelled: fine
                print(f"cancel {symbol} {o.id}: {e}")
        waited = 0.0
        while waited < wait_s:
            pos = self.positions().get(symbol)
            if pos is None:
                return True                              # a leg filled while cancelling: already flat
            avail = abs(float(getattr(pos, "qty_available", pos.qty) or 0))
            if not self._open_mcf(symbol, prefix) and avail >= abs(float(pos.qty)):
                break
            sleep(0.5)
            waited += 0.5
        for k in range(tries):
            try:
                self.client.close_position(symbol)
                return True
            except Exception as e:
                if symbol not in self.positions():
                    return True
                print(f"close {symbol} attempt {k + 1}/{tries} failed: {e}")
                for o in self._open_mcf(symbol, prefix):  # a leg re-appeared or was missed: cancel again
                    try:
                        self.client.cancel_order_by_id(o.id)
                    except Exception:
                        pass
                sleep(1.0 + k)
        return symbol not in self.positions()

    def orders_today_with_prefix(self, prefix: str, after) -> list:
        """All of today's orders (any status, with bracket/OTO legs) whose client_order_id starts with prefix."""
        from alpaca.trading.enums import QueryOrderStatus
        from alpaca.trading.requests import GetOrdersRequest

        out = self.client.get_orders(GetOrdersRequest(status=QueryOrderStatus.ALL, after=after, nested=True, limit=500))
        return [o for o in out if (o.client_order_id or "").startswith(prefix)]

    def _open_mcf(self, symbol: str, prefix: str):
        from alpaca.trading.enums import QueryOrderStatus
        from alpaca.trading.requests import GetOrdersRequest

        req = GetOrdersRequest(status=QueryOrderStatus.OPEN, nested=True, symbols=[symbol], limit=50)
        return [o for o in self.client.get_orders(req) if (o.client_order_id or "").startswith(prefix)]

    def move_stop(self, symbol: str, stop_price: float, prefix: str) -> None:
        """Move the open stop leg of this system's bracket/OTO order for `symbol`."""
        from alpaca.trading.requests import ReplaceOrderRequest

        for parent in self._open_mcf(symbol, prefix):
            for leg in parent.legs or []:
                if getattr(leg, "stop_price", None) is not None and str(getattr(leg.status, "value", leg.status)) in (
                        "new", "accepted", "held", "pending_new"):
                    self.client.replace_order_by_id(leg.id, ReplaceOrderRequest(stop_price=stop_price))
                    return
        raise RuntimeError(f"no open MCF stop leg for {symbol}")

    def cancel_orders_for_symbol(self, symbol: str, prefix: str) -> None:
        for o in self._open_mcf(symbol, prefix):
            self.client.cancel_order_by_id(o.id)

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
