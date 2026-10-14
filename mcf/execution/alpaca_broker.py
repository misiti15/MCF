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

        after = pd.Timestamp.now(tz="America/New_York").normalize().to_pydatetime()
        return [o for o in self._orders(QueryOrderStatus.ALL, after, symbol)
                if (o.client_order_id or "").startswith(prefix)]

    def _orders(self, status, after, symbol: str | None = None) -> list:
        """Every order (status filter, submitted after `after`, legs nested), paged - see page_orders."""
        from alpaca.trading.requests import GetOrdersRequest

        return page_orders(lambda until: self.client.get_orders(GetOrdersRequest(
            status=status, after=after, until=until, nested=True, limit=500, direction="desc",
            symbols=[symbol] if symbol else None)), after)

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

        return [o for o in self._orders(QueryOrderStatus.ALL, after) if (o.client_order_id or "").startswith(prefix)]

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

    # ---------------------------------------------------------------- per-lot (live.max_lots_per_symbol > 1)
    # A lot is one bracket on a symbol; its id is the parent's client order id (prefix-setup-symbol-YYYYMMDD[-HHMM]: with
    # live.same_setup_reentry one setup can hold several lots on a symbol, one per decision bar).
    # Positions are netted per symbol at the broker, so a lot is only ever changed through ITS OWN orders: its stop leg
    # is replaced, or its legs are cancelled and exactly its quantity is closed by an order whose client id is
    # lot_exit_coid(parent id) (so reconcile pairs the exit to the lot exactly).
    @staticmethod
    def lot_exit_coid(parent_coid: str) -> str:
        return f"{parent_coid}-x"

    def _lot_parent(self, symbol: str, parent_coid: str, prefix: str):
        for p in self._mcf_parents(prefix, symbol):
            if p.client_order_id == parent_coid:
                return p
        return None

    def move_lot_stop(self, symbol: str, parent_coid: str, stop_price: float, prefix: str) -> None:
        """Move the open stop leg of ONE lot (the bracket/OTO whose parent client id is parent_coid)."""
        from alpaca.trading.requests import ReplaceOrderRequest

        p = self._lot_parent(symbol, parent_coid, prefix)
        for leg in (getattr(p, "legs", None) or []) if p is not None else []:
            if getattr(leg, "stop_price", None) is not None and self._state(leg) in self.OPEN_STATES:
                self.client.replace_order_by_id(leg.id, ReplaceOrderRequest(stop_price=stop_price))
                return
        raise RuntimeError(f"no open stop leg for lot {parent_coid}")

    def close_mcf_lot(self, symbol: str, parent_coid: str, prefix: str, wait_s: float = 20.0, tries: int = 5,
                      sleep=None) -> bool:
        """Close ONE lot: cancel its own legs (never another lot's), wait until they are cancelled, then close exactly
        the lot's remaining quantity. Returns True when the lot is flat (also when one of its legs filled first or the
        entry never filled). Other lots on the symbol keep their shares and their resting stop/target legs."""
        import time as _t

        sleep = sleep or _t.sleep
        p = self._lot_parent(symbol, parent_coid, prefix)
        if p is None:
            raise RuntimeError(f"lot {parent_coid} not found")
        waited = 0.0
        if self._state(p) in self.OPEN_STATES:          # entry not (fully) filled yet: cancel it (and its legs)
            self._cancel([p.id])
            while waited < wait_s:
                p = self._lot_parent(symbol, parent_coid, prefix) or p
                if self._state(p) not in self.OPEN_STATES:
                    break
                sleep(0.5)
                waited += 0.5
        filled = abs(float(getattr(p, "filled_qty", 0) or 0))
        if filled <= 0:
            return True
        legs = getattr(p, "legs", None) or []
        if any(self._state(leg) == "filled" for leg in legs):
            return True                                   # its stop or target already closed it
        self._cancel([leg.id for leg in legs if self._state(leg) in self.OPEN_STATES])
        while True:
            p = self._lot_parent(symbol, parent_coid, prefix) or p
            legs = getattr(p, "legs", None) or []
            if any(self._state(leg) == "filled" for leg in legs):
                return True                               # a leg filled while cancelling: already flat
            if not any(self._state(leg) in self.OPEN_STATES for leg in legs):
                break
            if waited >= wait_s:
                return False                              # legs still hold the shares; retried next poll
            sleep(0.5)
            waited += 0.5
        qty = filled - sum(abs(float(getattr(leg, "filled_qty", 0) or 0)) for leg in legs)
        if qty <= 0:
            return True
        long = str(getattr(p.side, "value", p.side)).lower() == "buy"
        coid = self.lot_exit_coid(parent_coid)
        for k in range(tries):
            try:
                self._submit_lot_exit(symbol, qty, long, coid)
                return True
            except Exception as e:
                if "client_order_id" in str(e).lower() and "unique" in str(e).lower():
                    return True                           # an earlier attempt was accepted
                print(f"close lot {parent_coid} attempt {k + 1}/{tries} failed: {e}")
                sleep(1.0 + k)
        return False

    def _submit_lot_exit(self, symbol: str, qty: float, long: bool, coid: str):
        from alpaca.trading.enums import OrderSide, TimeInForce
        from alpaca.trading.requests import LimitOrderRequest, MarketOrderRequest

        side = OrderSide.SELL if long else OrderSide.BUY
        if self._market_open():
            return self.client.submit_order(MarketOrderRequest(symbol=symbol, qty=qty, side=side,
                                                               time_in_force=TimeInForce.DAY, client_order_id=coid))
        px = float(self.positions()[symbol].current_price)
        return self.client.submit_order(LimitOrderRequest(
            symbol=symbol, qty=qty, side=side, limit_price=round(px * (0.995 if long else 1.005), 2),
            time_in_force=TimeInForce.DAY, extended_hours=True, client_order_id=coid))

    def cancel_orders_for_symbol(self, symbol: str, prefix: str) -> None:
        self._cancel(self._open_mcf_ids(symbol, prefix))

    def cancel_orders_with_prefix(self, prefix: str) -> int:
        """Cancel this system's open orders, including the legs of filled brackets (this system's orders only)."""
        return self._cancel(self._open_mcf_ids(None, prefix))

    def flatten_all(self):
        self.client.cancel_orders()
        return self.client.close_all_positions(cancel_orders=True)

    def closed_orders_today(self, after):
        """Every closed order submitted after `after`, oldest first (legs nested), paged - see page_orders."""
        from alpaca.trading.enums import QueryOrderStatus

        return sorted(self._orders(QueryOrderStatus.CLOSED, after), key=lambda o: o.submitted_at)


def page_orders(fetch, after, page: int = 500, max_pages: int = 400) -> list:
    """Every order from fetch(until) (orders submitted after `after` and before `until`, None = now, NEWEST first).

    Alpaca's `limit` counts the nested bracket legs too, so a full page of 500 rows holds only ~170 entries: the old
    "stop at a short page" rule stopped after the first page, and an ascending query returned the oldest rows plus
    an arbitrary part of today (checked against the primary account 2026-10-14: one asc page since 10-06 returned
    202 of 289 entries and none of 10-12/10-13). Testing 1 on 2026-10-14: 9 filled lots (AMD: 1 of 2 lots of one
    flatten close) and the 10-12 ghosts were never booked. So: page newest -> oldest with `until` = oldest
    submitted_at seen + 1 ms (orders sharing that timestamp are fetched again and de-duplicated) and stop when a page
    brings nothing new or holds fewer than `page` rows counting its nested legs (on the primary account every full
    page held at least `limit` rows, the last page fewer). A leg whose parent sits on another page can also come back as a top-level row; those
    copies are dropped (the parent carries it)."""
    from datetime import timedelta

    out: dict[str, object] = {}
    until = None
    for _ in range(max_pages):
        got = list(fetch(until) or [])
        new = [o for o in got if str(o.id) not in out]
        for o in new:
            out[str(o.id)] = o
        rows = {str(o.id) for o in got} | {str(getattr(leg, "id", "")) for o in got
                                           for leg in (getattr(o, "legs", None) or [])}
        if not new or len(rows) < page:
            break
        oldest = min(o.submitted_at for o in got)
        until = oldest + timedelta(milliseconds=1)
    legs = {str(getattr(leg, "id", "")) for o in out.values() for leg in (getattr(o, "legs", None) or [])}
    return [o for i, o in out.items() if i not in legs]
