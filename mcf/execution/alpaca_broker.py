"""Alpaca paper/live broker adapter. Orders are bracket orders so every position
has a resting stop on the broker side even if this process dies."""

from __future__ import annotations

import os

import pandas as pd

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

    OPEN_STATES = {"new", "accepted", "held", "pending_new", "partially_filled", "pending_replace", "accepted_for_bidding"}

    @staticmethod
    def _state(o) -> str:
        return str(getattr(o.status, "value", o.status)).lower()

    def _mcf_parents(self, prefix: str, symbol: str | None = None) -> list:
        """Today's orders placed by this system (any status), with their bracket/OTO legs nested.

        The legs (stop-loss, take-profit) get broker-generated client ids, so they can only be found through
        their parent's prefixed id. Once the entry fills, the parent is no longer 'open' but its legs are -
        a status=OPEN query by prefix misses exactly the orders that hold the position's shares
        (2026-10-07: every 15:55 close was rejected because the take-profit legs were never cancelled)."""
        from alpaca.trading.enums import QueryOrderStatus
        from alpaca.trading.requests import GetOrdersRequest

        after = pd.Timestamp.now(tz="America/New_York").normalize().to_pydatetime()
        req = GetOrdersRequest(status=QueryOrderStatus.ALL, after=after, nested=True, limit=500,
                               symbols=[symbol] if symbol else None)
        return [o for o in self.client.get_orders(req) if (o.client_order_id or "").startswith(prefix)]

    def _open_mcf_ids(self, symbol: str | None, prefix: str) -> list:
        ids = []
        for p in self._mcf_parents(prefix, symbol):
            if self._state(p) in self.OPEN_STATES:
                ids.append(p.id)
            ids += [leg.id for leg in (getattr(p, "legs", None) or []) if self._state(leg) in self.OPEN_STATES]
        return ids

    def _cancel(self, ids) -> int:
        n = 0
        for oid in ids:
            try:
                self.client.cancel_order_by_id(oid)
                n += 1
            except Exception as e:                       # already filled/cancelled: fine
                print(f"cancel {oid}: {e}")
        return n

    def close_mcf_position(self, symbol: str, prefix: str, wait_s: float = 20.0, tries: int = 5, sleep=None) -> bool:
        """Cancel this system's open orders on `symbol` (parents AND their legs), wait until the broker has
        released the shares, then close. Outside regular hours a market close would only queue for the next
        open, so an extended-hours marketable limit is used instead. Returns True when the position is gone
        (or a closing order is working after hours). Only this system's orders are touched (shared account)."""
        import time as _t

        sleep = sleep or _t.sleep
        self._cancel(self._open_mcf_ids(symbol, prefix))
        waited = 0.0
        while waited < wait_s:
            pos = self.positions().get(symbol)
            if pos is None:
                return True                              # a leg filled while cancelling: already flat
            avail = abs(float(getattr(pos, "qty_available", pos.qty) or 0))
            if avail >= abs(float(pos.qty)):
                break
            sleep(0.5)
            waited += 0.5
        for k in range(tries):
            try:
                if self._market_open():
                    self.client.close_position(symbol)
                    return True
                return self._close_after_hours(symbol, prefix)
            except Exception as e:
                if symbol not in self.positions():
                    return True
                print(f"close {symbol} attempt {k + 1}/{tries} failed: {e}")
                self._cancel(self._open_mcf_ids(symbol, prefix))   # a leg was missed or re-appeared
                sleep(1.0 + k)
        return symbol not in self.positions()

    def _market_open(self) -> bool:
        try:
            return bool(self.client.get_clock().is_open)
        except Exception:
            return True

    def _close_after_hours(self, symbol: str, prefix: str) -> bool:
        from alpaca.trading.enums import OrderSide, TimeInForce
        from alpaca.trading.requests import LimitOrderRequest

        pos = self.positions().get(symbol)
        if pos is None:
            return True
        qty = abs(float(pos.qty))
        long = float(pos.qty) > 0
        px = float(pos.current_price)
        limit = round(px * (0.995 if long else 1.005), 2)
        self.client.submit_order(LimitOrderRequest(
            symbol=symbol, qty=qty, side=OrderSide.SELL if long else OrderSide.BUY, limit_price=limit,
            time_in_force=TimeInForce.DAY, extended_hours=True,
            client_order_id=f"{prefix}flatten-{symbol}-{pd.Timestamp.now(tz='America/New_York'):%Y%m%d%H%M%S}"))
        print(f"close {symbol}: after-hours limit {limit} ({'sell' if long else 'buy'} {qty:g})")
        return True

    def orders_today_with_prefix(self, prefix: str, after) -> list:
        """All of today's orders (any status, with bracket/OTO legs) whose client_order_id starts with prefix."""
        from alpaca.trading.enums import QueryOrderStatus
        from alpaca.trading.requests import GetOrdersRequest

        out = self.client.get_orders(GetOrdersRequest(status=QueryOrderStatus.ALL, after=after, nested=True, limit=500))
        return [o for o in out if (o.client_order_id or "").startswith(prefix)]

    def _open_mcf(self, symbol: str, prefix: str):
        return self._mcf_parents(prefix, symbol)

    def move_stop(self, symbol: str, stop_price: float, prefix: str) -> None:
        """Move the open stop leg of this system's bracket/OTO order for `symbol`."""
        from alpaca.trading.requests import ReplaceOrderRequest

        for parent in self._open_mcf(symbol, prefix):
            for leg in parent.legs or []:
                if getattr(leg, "stop_price", None) is not None and self._state(leg) in self.OPEN_STATES:
                    self.client.replace_order_by_id(leg.id, ReplaceOrderRequest(stop_price=stop_price))
                    return
        raise RuntimeError(f"no open MCF stop leg for {symbol}")

    def cancel_orders_for_symbol(self, symbol: str, prefix: str) -> None:
        self._cancel(self._open_mcf_ids(symbol, prefix))

    def cancel_orders_with_prefix(self, prefix: str) -> int:
        """Cancel this system's open orders, including the legs of filled brackets (this system's orders only)."""
        return self._cancel(self._open_mcf_ids(None, prefix))

    def flatten_all(self):
        self.client.cancel_orders()
        return self.client.close_all_positions(cancel_orders=True)

    def closed_orders_today(self, after):
        from alpaca.trading.enums import QueryOrderStatus
        from alpaca.trading.requests import GetOrdersRequest

        return self.client.get_orders(GetOrdersRequest(status=QueryOrderStatus.CLOSED, after=after, nested=True, limit=500))
