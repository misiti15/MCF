"""Alpaca paper/live broker adapter. Orders are bracket orders so every position
has a resting stop on the broker side even if this process dies."""

from __future__ import annotations

import os

import pandas as pd

from ..strategies.base import Signal


class _RetryGets:
    """Retry the client's read-only get_* calls on a dropped connection or timeout (2026-10-19: one
    RemoteDisconnected on get_all_positions ended the gen account's job). Orders, cancels and replaces are never
    retried here (a retry could duplicate them)."""

    def __init__(self, client, tries: int = 3, sleep=None):
        import time

        self._c, self._tries, self._sleep = client, tries, sleep or time.sleep

    def __getattr__(self, name):
        f = getattr(self._c, name)
        if not (name.startswith("get_") and callable(f)):
            return f

        def call(*a, **kw):
            import requests

            for i in range(self._tries):
                try:
                    return f(*a, **kw)
                except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
                    if i == self._tries - 1:
                        raise
                    print(f"broker {name}: {e.__class__.__name__}, retry {i + 1}")
                    self._sleep(1.0 * (i + 1))
        return call


class AlpacaBroker:
    def __init__(self, paper: bool = True):
        from alpaca.trading.client import TradingClient

        # Orders go to ALPACA_TRADE_* when set (the Testing account); market data always uses ALPACA_API_KEY (SIP plan).
        k = os.environ.get("ALPACA_TRADE_API_KEY") or os.environ["ALPACA_API_KEY"]
        sec = os.environ.get("ALPACA_TRADE_SECRET_KEY") or os.environ["ALPACA_SECRET_KEY"]
        self.client = _RetryGets(TradingClient(k, sec, paper=paper))

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
        """Move the open stop of this system's order for `symbol`: a bracket/OTO stop leg, or a scaled lot's
        protective stop (its OCO stop leg or plain stop order)."""
        orders = self._open_mcf(symbol, prefix)
        for parent in orders:
            base = _protect_base(parent.client_order_id)       # a scaled lot's protective order (-p / -p<N>)
            cands = ([parent] if base else []) + list(parent.legs or [])
            for leg in cands:
                if getattr(leg, "stop_price", None) is not None and self._state(leg) in self.OPEN_STATES:
                    self._replace_stop(leg, stop_price, orders, base or parent.client_order_id)
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
        """Move the open stop of ONE lot: its bracket/OTO stop leg, or - once the lot has been scaled out - the stop of
        its protective order (lot_protect_coid: the OCO's stop leg, or the plain stop order itself)."""
        orders = self._mcf_parents(prefix, symbol)
        p = next((o for o in orders if o.client_order_id == parent_coid), None)
        o = self._lot_stop_order(orders, p, parent_coid) if p is not None else None
        if o is None:
            raise RuntimeError(f"no open stop leg for lot {parent_coid}")
        self._replace_stop(o, stop_price, orders, parent_coid)

    def _replace_stop(self, o, stop_price: float, orders, parent_coid: str) -> None:
        """Replace a stop's price. A plain protective stop is a top-level order known only by its client id, so its
        replacement carries the next id of the lot's protect series (<parent>-p1, -p2, ...); legs keep broker ids."""
        from alpaca.trading.requests import ReplaceOrderRequest

        kw = {"stop_price": stop_price}
        if self._is_protect(getattr(o, "client_order_id", None), parent_coid):
            k = len(self._protections(orders, parent_coid))
            kw["client_order_id"] = f"{self.lot_protect_coid(parent_coid)}{k}"
        self.client.replace_order_by_id(o.id, ReplaceOrderRequest(**kw))

    @classmethod
    def _lot_stop_order(cls, orders, parent, parent_coid: str):
        """The working stop that protects a lot: a stop leg of its entry bracket/OTO, else (after a scale-out) the stop
        of its protective order - the OCO's stop leg or the plain stop order. None when it has none."""
        cands = list(getattr(parent, "legs", None) or [])
        for o in cls._protections(orders, parent_coid):
            cands += [o, *(getattr(o, "legs", None) or [])]
        return next((o for o in cands if getattr(o, "stop_price", None) is not None
                     and cls._state(o) in cls.OPEN_STATES), None)

    def close_mcf_lot(self, symbol: str, parent_coid: str, prefix: str, wait_s: float = 20.0, tries: int = 5,
                      sleep=None) -> bool:
        """Close ONE lot: cancel its own legs and its protective order after a scale-out (never another lot's), wait
        until they are cancelled, then close exactly the lot's remaining quantity. Returns True when the lot is flat
        (also when one of its legs / its protection filled first or the entry never filled). Other lots on the symbol
        keep their shares and their resting stop/target legs."""
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
        orders = self._mcf_parents(prefix, symbol)
        prot = [x for o in self._protections(orders, parent_coid) for x in (o, *(getattr(o, "legs", None) or []))]
        if any(self._state(x) == "filled" for x in prot):
            return True                                   # its protective stop/target closed the rest
        self._cancel([x.id for x in [*legs, *prot] if self._state(x) in self.OPEN_STATES])
        while True:
            orders = self._mcf_parents(prefix, symbol)
            p = next((o for o in orders if o.client_order_id == parent_coid), None) or p
            legs = getattr(p, "legs", None) or []
            prot = [x for o in self._protections(orders, parent_coid) for x in (o, *(getattr(o, "legs", None) or []))]
            if any(self._state(x) == "filled" for x in [*legs, *prot]):
                return True                               # a leg filled while cancelling: already flat
            if not any(self._state(x) in self.OPEN_STATES for x in [*legs, *prot]):
                break
            if waited >= wait_s:
                return False                              # legs still hold the shares; retried next poll
            sleep(0.5)
            waited += 0.5
        qty = filled - sum(self._fq(leg) for leg in legs) - self._child_fills(orders, parent_coid)
        if qty <= 0:
            return True
        long = str(getattr(p.side, "value", p.side)).lower() == "buy"
        coid = self.lot_exit_coid(parent_coid)
        for k in range(tries):
            try:
                self._submit_lot_exit(symbol, qty, long, coid)
                return True
            except Exception as e:
                if self._dup(e):
                    return True                           # an earlier attempt was accepted
                print(f"close lot {parent_coid} attempt {k + 1}/{tries} failed: {e}")
                sleep(1.0 + k)
        return False

    # ---------------------------------------------------------------- live scale-out (per setup, opt-in)
    # A setup with `live_scale_out: true` banks part of a lot at +scale_out_r R and moves the rest to breakeven, the
    # backtest engine's scale-out (simulate()). Alpaca rejects a qty change on bracket/OTO legs ("qty cannot be changed
    # for advanced orders", 2026-10-19), so the lot's own orders change instead (owner-approved 2026-10-19):
    #   1. cancel the lot's stop + target legs and wait until they are cancelled and the shares released;
    #   2. sell (buy for a short) the banked shares, client id lot_scale_coid(parent id) = <parent>-s;
    #   3. protect the rest with client id lot_protect_coid(parent id) = <parent>-p: an OCO exit (target limit + stop at
    #      breakeven) when the lot had a target, else a plain stop at breakeven. If that order is refused, the rest is
    #      closed at market (<parent>-u) - shares are never left without a stop.
    # Reconcile pairs -s, -p (and its legs / replacements) and -u to the lot (one journal row, exit_parts).
    @staticmethod
    def lot_scale_coid(parent_coid: str) -> str:
        return f"{parent_coid}-s"

    @staticmethod
    def lot_protect_coid(parent_coid: str) -> str:
        return f"{parent_coid}-p"

    @staticmethod
    def lot_unprotected_coid(parent_coid: str) -> str:
        return f"{parent_coid}-u"

    @classmethod
    def _is_protect(cls, coid, parent_coid: str) -> bool:
        """<parent>-p (the protective order) or <parent>-p<N> (a plain protective stop after its N-th stop move)."""
        c, base = coid or "", cls.lot_protect_coid(parent_coid)
        return c == base or (c.startswith(base) and c[len(base):].isdigit())

    @classmethod
    def _protections(cls, orders, parent_coid: str) -> list:
        return [o for o in orders if cls._is_protect(getattr(o, "client_order_id", None), parent_coid)]

    @staticmethod
    def _fq(o) -> float:
        return abs(float(getattr(o, "filled_qty", 0) or 0))

    @staticmethod
    def _dup(e) -> bool:
        return "client_order_id" in str(e).lower() and "unique" in str(e).lower()

    @classmethod
    def _child_fills(cls, orders, parent_coid: str) -> float:
        """Shares of a lot closed by its own scale-out (-s), protection (-p, its legs, its stop moves) and -u orders."""
        own = {cls.lot_scale_coid(parent_coid), cls.lot_unprotected_coid(parent_coid)}
        n = 0.0
        for o in orders:
            c = getattr(o, "client_order_id", None)
            if c in own:
                n += cls._fq(o)
            elif cls._is_protect(c, parent_coid):
                n += cls._fq(o) + sum(cls._fq(leg) for leg in getattr(o, "legs", None) or [])
        return n

    @staticmethod
    def scale_split(qty: float, frac: float) -> int:
        """Shares to bank: floor(qty x frac), at least 1 and leaving at least 1; 0 (no scale-out) when qty < 2."""
        import math

        q = int(round(float(qty)))
        if q < 2:
            return 0
        return min(q - 1, max(1, int(math.floor(q * float(frac) + 1e-9))))

    def lot_fill(self, symbol: str, parent_coid: str, prefix: str) -> tuple[float, float] | None:
        """(filled qty, average fill price) of a lot's entry once it is completely filled; None before that."""
        p = self._lot_parent(symbol, parent_coid, prefix)
        if p is None or self._state(p) in self.OPEN_STATES or getattr(p, "filled_avg_price", None) is None:
            return None
        q = abs(float(getattr(p, "filled_qty", 0) or 0))
        return (q, float(p.filled_avg_price)) if q > 0 else None

    CANCELLING = {"pending_cancel"}
    DEAD = {"canceled", "cancelled", "expired", "rejected", "done_for_day", "replaced"}

    def scale_out_lot(self, symbol: str, parent_coid: str, frac: float, prefix: str, tries: int = 4,
                      sleep=None, wait_s: float = 10.0) -> dict:
        """Bank `frac` of ONE lot and protect the rest at breakeven (steps 1-3 above). Idempotent, retried next poll.
        Returns {"status": ...}: "scaled" (with qty, left, stop), "already" (scaled earlier; a missing protection is
        placed now - restart between steps 2 and 3), "closed" (a leg filled first / no working legs / never filled),
        "pending" (entry not filled yet), "skip" (qty < 2, or a lot re-protected without a scale-out), "partial" (legs
        not released yet - retry), "closed_unprotected" (protection refused: the rest was closed at market), "error"."""
        import time as _t

        sleep = sleep or _t.sleep
        orders = self._mcf_parents(prefix, symbol)
        p = next((o for o in orders if o.client_order_id == parent_coid), None)
        if p is None:
            raise RuntimeError(f"lot {parent_coid} not found")
        coid = self.lot_scale_coid(parent_coid)
        s_ord = next((o for o in orders if o.client_order_id == coid), None)
        prots = self._protections(orders, parent_coid)
        ended = any(o.client_order_id in (self.lot_exit_coid(parent_coid), self.lot_unprotected_coid(parent_coid))
                    for o in orders)
        if self._state(p) in self.OPEN_STATES:
            return {"status": "pending"}
        filled = abs(float(getattr(p, "filled_qty", 0) or 0))
        if filled <= 0 or getattr(p, "filled_avg_price", None) is None:
            return {"status": "closed"}
        legs = getattr(p, "legs", None) or []
        long = str(getattr(p.side, "value", p.side)).lower() == "buy"
        side = 1 if long else -1
        be = round(float(p.filled_avg_price), 2)
        target = next((float(leg.limit_price) for leg in legs if getattr(leg, "limit_price", None) is not None), None)
        stop_leg = next((leg for leg in legs if getattr(leg, "stop_price", None) is not None), None)
        old_stop = float(stop_leg.stop_price) if stop_leg is not None else be
        new_stop = be if side * (be - old_stop) > 1e-9 else old_stop      # only ever tightened
        live = [leg for leg in legs if self._state(leg) in self.OPEN_STATES]
        if prots or ended:
            cur = self._lot_stop_order(orders, p, parent_coid)
            st = float(cur.stop_price) if cur is not None else new_stop
            return {"status": "already", "stop": st} if s_ord is not None else {"status": "skip", "stop": st}
        if s_ord is not None:                             # banked, rest not protected yet (restart / failed step 3)
            if live:
                return {"status": "already", "stop": new_stop}   # legs still working: nothing to resume
            sq = self._fq(s_ord) if self._state(s_ord) in self.DEAD else abs(float(s_ord.qty or 0))
            rem = int(round(filled - sum(self._fq(leg) for leg in legs) - sq))
            pos = self.positions().get(symbol)
            held = side * float(pos.qty) if pos is not None else 0.0
            rem = int(min(rem, max(0.0, held)))
            if rem <= 0:
                return {"status": "already", "stop": new_stop}
            print(f"scale-out {parent_coid}: banked order exists, protecting the remaining {rem} (resume)")
            st = self._protect_rest(symbol, parent_coid, rem, long, new_stop, target, tries, sleep)
            return {"status": "already" if st == "ok" else st, "stop": new_stop, "resumed": True,
                    **({"error": "protection and market close both refused"} if st == "error" else {})}
        if any(self._state(leg) == "filled" or self._fq(leg) > 0 for leg in legs):
            return {"status": "closed"}                   # its stop or target (partly) closed it first
        mine = parent_coid in self.__dict__.setdefault("_scale_cancelled", set())
        if not live and not mine:
            return {"status": "closed"}                   # legs cancelled (flatten / time stop in progress)
        n = self.scale_split(filled, frac)
        if n <= 0:
            return {"status": "skip", "qty": filled}
        rem = int(round(filled)) - n

        # 1. cancel the stop + target legs, wait until cancelled and the shares are no longer held for them
        self._scale_cancelled.add(parent_coid)
        self._cancel([leg.id for leg in live])
        waited = 0.0
        while True:
            p = self._lot_parent(symbol, parent_coid, prefix) or p
            legs = getattr(p, "legs", None) or []
            got = sum(self._fq(leg) for leg in legs)
            working = any(self._state(leg) in self.OPEN_STATES | self.CANCELLING for leg in legs)
            if got >= filled - 1e-9 or any(self._state(leg) == "filled" for leg in legs):
                return {"status": "closed"}               # a leg filled while cancelling: nothing else to do
            if not working:
                if got > 0:                               # partly filled, rest cancelled: re-protect what is left
                    left = int(round(filled - got))
                    st = self._protect_rest(symbol, parent_coid, left, long, old_stop, target, tries, sleep)
                    return {"status": "closed" if st == "ok" else st, "left": left}
                pos = self.positions().get(symbol)
                if pos is None or side * float(pos.qty) <= 0:
                    return {"status": "closed"}           # flat already (another process closed the symbol)
                avail = side * float(getattr(pos, "qty_available", None) or pos.qty)
                if avail >= filled - 1e-9:
                    break
            if waited >= wait_s:
                return {"status": "partial", "qty": n, "left": rem, "stop": new_stop,
                        "error": "legs not released yet after cancel"}
            sleep(0.5)
            waited += 0.5

        # 2. the banked shares
        err = None
        for k in range(tries):
            try:
                self._submit_lot_exit(symbol, n, long, coid)
                err = None
                break
            except Exception as e:
                if self._dup(e):
                    err = None
                    break
                err = e
                print(f"scale-out {parent_coid} attempt {k + 1}/{tries} failed: {e}")
                sleep(0.5 + 0.5 * k)
        if err is not None:                               # not banked: put the lot's own stop/target back
            st = self._protect_rest(symbol, parent_coid, int(round(filled)), long, old_stop, target, tries, sleep)
            return {"status": st if st != "ok" else "error",
                    "error": f"banked order refused ({str(err)[:120]}); lot re-protected at its stop/target"
                    if st == "ok" else f"banked order refused ({str(err)[:120]})"}

        # 3. protect the rest: OCO (target + breakeven stop) or a plain breakeven stop
        st = self._protect_rest(symbol, parent_coid, rem, long, new_stop, target, tries, sleep)
        out = {"qty": n, "left": rem, "stop": new_stop, "entry": float(p.filled_avg_price)}
        if st == "ok":
            return {"status": "scaled", **out}
        return {"status": st, **out, **({"error": "protection and market close both refused"} if st == "error" else {})}

    def _protect_rest(self, symbol: str, parent_coid: str, qty: int, long: bool, stop: float, target, tries: int,
                      sleep) -> str:
        """Place the lot's protective order (lot_protect_coid) for `qty` shares; "ok" once accepted. If the broker keeps
        refusing it, close those shares at market (lot_unprotected_coid) -> "closed_unprotected"; "error" when even
        that fails (retried next poll: the resume path in scale_out_lot)."""
        pc = self.lot_protect_coid(parent_coid)
        for k in range(tries):
            try:
                self._submit_protection(symbol, qty, long, stop, target, pc)
                return "ok"
            except Exception as e:
                if self._dup(e):
                    return "ok"
                print(f"protect {parent_coid} ({qty} @ stop {stop}) attempt {k + 1}/{tries} failed: {e}")
                sleep(0.5 + 0.5 * k)
        uc = self.lot_unprotected_coid(parent_coid)
        for k in range(tries):
            try:
                self._submit_lot_exit(symbol, qty, long, uc)
                print(f"PROTECT FAILED {parent_coid}: closed the remaining {qty} at market")
                return "closed_unprotected"
            except Exception as e:
                if self._dup(e):
                    return "closed_unprotected"
                print(f"close unprotected {parent_coid} attempt {k + 1}/{tries} failed: {e}")
                sleep(0.5 + 0.5 * k)
        return "error"

    def _submit_protection(self, symbol: str, qty: int, long: bool, stop: float, target, coid: str):
        """Exit order for a lot's remaining shares: OCO (limit target + stop; Alpaca's OCO is a limit parent with a
        stop_loss) when there is a target on the right side of the stop, else a plain stop. Day orders, whole shares;
        a short lot's exits are buys."""
        from alpaca.trading.enums import OrderClass, OrderSide, TimeInForce
        from alpaca.trading.requests import LimitOrderRequest, StopLossRequest, StopOrderRequest, TakeProfitRequest

        side = OrderSide.SELL if long else OrderSide.BUY
        kw = dict(symbol=symbol, qty=int(qty), side=side, time_in_force=TimeInForce.DAY, client_order_id=coid)
        if target is not None and (1 if long else -1) * (float(target) - float(stop)) > 0:
            return self.client.submit_order(LimitOrderRequest(
                **kw, order_class=OrderClass.OCO, take_profit=TakeProfitRequest(limit_price=round(float(target), 2)),
                stop_loss=StopLossRequest(stop_price=round(float(stop), 2))))
        return self.client.submit_order(StopOrderRequest(**kw, stop_price=round(float(stop), 2)))

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


def _protect_base(coid) -> str | None:
    """Parent client id of a lot's protective order id (<parent>-p or <parent>-p<N>); None for any other id."""
    import re

    m = re.match(r"^(?P<base>.+)-p\d*$", coid or "")
    return m["base"] if m else None


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
