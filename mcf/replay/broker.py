"""Simulated Alpaca for replays: a TradingClient stand-in (the surface mcf.execution.alpaca_broker.AlpacaBroker uses)
that fills orders from the recorded 1-minute bars of one session, a market-data stand-in for the latest quote, and a
synthetic clock. Built on the ideas of mcf.execution.drill.DrillAlpaca (nested bracket legs, netted positions, cancels,
stop replaces, market closes), plus a fill engine.

Fill model (each poll the runner sees completed bars only; orders act on the bars from the poll's minute on):
  market      the open of the bar of the minute it is submitted in (the next bar after the decision bar; a symbol
              without that bar fills at the open of its next bar). Exits: the same.
  stop        from the bar its parent filled in: a bar whose low (long) / high (short) reaches the stop fills at the stop,
              or at the open when a later bar gaps through it (backtest rule: stop first inside a bar).
  limit       target legs / OCO targets. `limit_fill="through"` (default, research rule): the bar must trade through the
              limit by a cent (high >= limit + 0.01 for a sell); a bar that only touches it is recorded in `touches`
              (the touch-fill the paper broker gives). `"touch"`: high >= limit fills (Alpaca paper behaviour).
  costs       `fills="costs"` (default): production costs from config costs (mcf.backtest.engine.Costs: slippage per
              share + bps on entries and non-limit exits, stop_slippage_per_share extra on stop fills, extended-tier
              names extended_slippage_per_share). `fills="paper"`: raw prices (what Alpaca paper fills), for comparing
              with the live paper journals.
No network; nothing here can reach a broker. Educational only - not financial advice."""

from __future__ import annotations

import itertools
from datetime import timedelta
from types import SimpleNamespace as NS

import numpy as np
import pandas as pd

NY = "America/New_York"
OPEN = {"new", "held", "accepted", "pending_new", "partially_filled"}


def _v(x) -> str:
    return str(getattr(x, "value", x)).lower()


class SimClock:
    """The replay's wall clock (ET). sleep() advances it; nothing waits for real."""

    def __init__(self, now: pd.Timestamp):
        self.now = pd.Timestamp(now).tz_convert(NY)

    def sleep(self, s: float):
        self.now = self.now + pd.Timedelta(seconds=float(s))

    def epoch(self) -> float:
        return self.now.timestamp()


class SimTime:
    """Drop-in for the `time` module inside mcf.execution.runner during a replay (time / sleep / perf_counter)."""

    def __init__(self, clock: SimClock):
        import time as _real

        self._clock, self._real = clock, _real

    def time(self) -> float:
        return self._clock.epoch()

    def sleep(self, s: float):
        self._clock.sleep(s)

    def __getattr__(self, name):
        return getattr(self._real, name)


class SimMarket:
    """One session's 1-minute bars as dense arrays: minute k (0 = 09:30) -> open/high/low/close/volume (NaN = no bar)."""

    def __init__(self, day, bars: dict[str, pd.DataFrame]):
        self.day = pd.Timestamp(str(day)).date()
        self.t0 = pd.Timestamp(f"{self.day} 09:30", tz=NY)
        self.arr: dict[str, np.ndarray] = {}
        for sym, b in bars.items():
            if b is None or b.empty:
                continue
            k = ((b.index - self.t0) // pd.Timedelta(minutes=1)).to_numpy()
            ok = (k >= 0) & (k < 390)
            a = np.full((390, 5), np.nan)
            a[k[ok]] = b[["open", "high", "low", "close", "volume"]].to_numpy(float)[ok]
            self.arr[sym] = a

    def minute(self, now: pd.Timestamp) -> int:
        return int((pd.Timestamp(now) - self.t0) // pd.Timedelta(minutes=1))

    def bar(self, sym: str, k: int):
        a = self.arr.get(sym)
        if a is None or not 0 <= k < 390 or np.isnan(a[k, 0]):
            return None
        return a[k]

    def last_close(self, sym: str, k: int):
        """Close of the latest bar before minute k (the last completed bar at a poll in minute k)."""
        a = self.arr.get(sym)
        if a is None:
            return None
        c = a[: max(0, min(k, 390)), 3]
        c = c[~np.isnan(c)]
        return float(c[-1]) if len(c) else None

    def bar_time(self, k: int) -> pd.Timestamp:
        return self.t0 + pd.Timedelta(minutes=int(k))


class SimTradingClient:
    """The TradingClient calls AlpacaBroker makes, against SimMarket. One instance = one account, one session."""

    def __init__(self, clock: SimClock, market: SimMarket, costs: dict | None = None, fills: str = "costs",
                 limit_fill: str = "through", equity: float = 100_000.0, shortable: dict | None = None,
                 extended: set | None = None):
        if fills not in ("costs", "paper") or limit_fill not in ("through", "touch"):
            raise ValueError("fills: costs|paper, limit_fill: through|touch")
        self.clock, self.mkt = clock, market
        c = costs or {}
        self.bps = float(c.get("slippage_bps", 1.0)) if fills == "costs" else 0.0
        self.ps = float(c.get("slippage_per_share", 0.01)) if fills == "costs" else 0.0
        self.ps_ext = float(c.get("extended_slippage_per_share", 0.03)) if fills == "costs" else 0.0
        self.stop_extra = float(c.get("stop_slippage_per_share", 0.02)) if fills == "costs" else 0.0
        self.fills, self.limit_fill = fills, limit_fill
        self.equity = float(equity)
        self.shortable = shortable or {}
        self.extended = extended or set()
        self.orders: list = []
        self.by_id: dict[str, object] = {}
        self.pos: dict[str, float] = {}
        self.avg: dict[str, float] = {}
        self.done_min = -1                 # bars up to this minute have been applied to working orders
        self.touches: list[dict] = []      # limit touched but not traded through (limit_fill="through")
        self.fill_log: list[dict] = []
        self._ids = itertools.count(1)
        self._us = itertools.count(1)

    # ------------------------------------------------------------------ helpers
    def _now_utc(self):
        # unique, increasing submission stamps (several orders per poll), as the broker's own timestamps are
        return (self.clock.now + pd.Timedelta(microseconds=next(self._us))).tz_convert("UTC").to_pydatetime()

    def _new(self, **kw):
        o = NS(id=f"sim-{next(self._ids)}", client_order_id=None, symbol=None, side=None, qty="0", filled_qty="0",
               filled_avg_price=None, status="new", order_type="market", order_class="simple", legs=None,
               replaces=None, submitted_at=self._now_utc(), filled_at=None, canceled_at=None, stop_price=None,
               limit_price=None, extended_hours=False, _active=None, _role="exit", _parent=None)
        for k, v in kw.items():
            setattr(o, k, v)
        self.by_id[o.id] = o
        return o

    def _all(self):
        for o in self.orders:
            yield o
            yield from o.legs or []

    def _side_sign(self, o) -> int:
        return 1 if _v(o.side) == "buy" else -1

    def _slip_ps(self, sym) -> float:
        return self.ps_ext if sym in self.extended else self.ps

    def _cost(self, px: float, sym: str, side: int, kind: str) -> float:
        """Fill price after costs for an order of side `side` (+1 buy, -1 sell). kind: market | stop | limit."""
        if kind == "limit":
            return float(px)
        extra = self.stop_extra if kind == "stop" else 0.0
        return float(px * (1 + side * self.bps / 1e4) + side * (self._slip_ps(sym) + extra))

    def _fill(self, o, px: float, k: int, kind: str):
        side = self._side_sign(o)
        q = abs(float(o.qty)) - abs(float(o.filled_qty or 0))
        fp = round(self._cost(px, o.symbol, side, kind), 6)
        o.filled_qty, o.filled_avg_price, o.status = str(abs(float(o.qty))), str(fp), "filled"
        o.filled_at = (self.mkt.bar_time(k) + pd.Timedelta(seconds=1)).tz_convert("UTC").to_pydatetime()
        cur = self.pos.get(o.symbol, 0.0)
        new = cur + side * q
        if cur == 0 or np.sign(cur) == side:                       # opening / adding: average entry price
            self.avg[o.symbol] = (abs(cur) * self.avg.get(o.symbol, 0.0) + q * fp) / max(abs(new), 1e-9)
        if abs(new) < 1e-9:
            self.pos.pop(o.symbol, None)
            self.avg.pop(o.symbol, None)
        else:
            self.pos[o.symbol] = new
        self.fill_log.append({"id": o.id, "coid": o.client_order_id, "symbol": o.symbol, "side": side, "qty": q,
                              "px": fp, "raw": float(px), "kind": kind, "minute": k, "role": o._role})
        if o._role == "entry":
            for leg in o.legs or []:
                leg._active = k                                    # legs work from the entry bar on
        par = o._parent
        if par is not None:                                        # a leg filled: its sibling (OCO) is cancelled
            for leg in par.legs or []:
                if leg is not o and leg.status in OPEN:
                    leg.status, leg.canceled_at = "canceled", o.filled_at
            if par._role == "oco" and par.status in OPEN:          # an OCO's stop leg filled: its limit is done too
                par.status, par.canceled_at = "canceled", o.filled_at
        for leg in (o.legs or []) if o._role == "oco" else []:     # OCO parent (target) filled: cancel its stop leg
            if leg.status in OPEN:
                leg.status, leg.canceled_at = "canceled", o.filled_at

    def _try(self, o, k: int, bar, entry_bar: bool):
        """Apply bar k to a working order. Returns True when it filled."""
        op, hi, lo = float(bar[0]), float(bar[1]), float(bar[2])
        side = self._side_sign(o)
        t = _v(o.order_type)
        if t == "market":
            self._fill(o, op, k, "market")
            return True
        if t == "stop":
            sp = float(o.stop_price)
            if side == -1 and lo <= sp:                            # sell stop (long exit)
                self._fill(o, op if (op < sp and not entry_bar) else sp, k, "stop")
                return True
            if side == 1 and hi >= sp:                             # buy stop (short exit)
                self._fill(o, op if (op > sp and not entry_bar) else sp, k, "stop")
                return True
            return False
        if t == "limit":
            lp = float(o.limit_price)
            tick = 0.01 if self.limit_fill == "through" else 0.0
            if side == -1:
                if (op > lp and not entry_bar) or hi >= lp + tick - 1e-9:
                    self._fill(o, op if (op > lp and not entry_bar) else lp, k, "limit")
                    return True
                if hi >= lp - 1e-9:
                    self.touches.append({"id": o.id, "parent": getattr(o._parent, "client_order_id", None),
                                         "coid": o.client_order_id, "symbol": o.symbol, "minute": k, "limit": lp})
            else:
                if (op < lp and not entry_bar) or lo <= lp - tick + 1e-9:
                    self._fill(o, op if (op < lp and not entry_bar) else lp, k, "limit")
                    return True
                if lo <= lp + 1e-9:
                    self.touches.append({"id": o.id, "parent": getattr(o._parent, "client_order_id", None),
                                         "coid": o.client_order_id, "symbol": o.symbol, "minute": k, "limit": lp})
            return False
        return False

    def advance(self):
        """Apply every completed bar (minute < the clock's minute) to the working orders, in time order. Within a bar a
        lot's stop is tried before its target (conservative, as the backtester)."""
        cur = self.mkt.minute(self.clock.now)
        for k in range(self.done_min + 1, min(cur, 390)):
            work = [o for o in self._all() if o.status in OPEN and o._active is not None and o._active <= k]
            # stops first, then limits, then markets (market orders waiting for a bar)
            work.sort(key=lambda o: {"stop": 0, "limit": 1}.get(_v(o.order_type), 2))
            for o in work:
                if o.status not in OPEN:
                    continue                                       # cancelled by a sibling earlier in this bar
                bar = self.mkt.bar(o.symbol, k)
                if bar is None:
                    continue
                par = o._parent
                entry_bar = par is not None and par.filled_at is not None and \
                    self.mkt.minute(pd.Timestamp(par.filled_at).tz_convert(NY)) == k
                self._try(o, k, bar, entry_bar)
            self.done_min = k

    def _reserved(self, sym) -> float:
        """Shares held for working exit orders (a bracket's legs hold its filled quantity once, as the broker does)."""
        n = 0.0
        for o in self.orders:
            if o.symbol != sym:
                continue
            if o._role == "entry":
                if o.status == "filled" and any(leg.status in OPEN for leg in o.legs or []):
                    n += abs(float(o.filled_qty)) - sum(abs(float(leg.filled_qty or 0)) for leg in o.legs or [])
            elif o.status in OPEN or any(leg.status in OPEN for leg in o.legs or []):
                n += abs(float(o.qty)) - abs(float(o.filled_qty or 0))
        return n

    # ------------------------------------------------------------------ TradingClient surface
    def get_account(self):
        return NS(equity=str(self.equity), cash=str(self.equity), buying_power=str(self.equity * 4))

    def get_clock(self):
        self.advance()
        now = self.clock.now
        o, c = now.normalize() + pd.Timedelta(hours=9, minutes=30), now.normalize() + pd.Timedelta(hours=16)
        is_open = o <= now < c
        nxt = o if now < o else o + pd.Timedelta(days=1)
        return NS(is_open=is_open, timestamp=now.tz_convert("UTC").to_pydatetime(),
                  next_open=nxt.tz_convert("UTC").to_pydatetime(), next_close=c.tz_convert("UTC").to_pydatetime())

    def get_asset(self, sym):
        ok = self.shortable.get(sym, (True, True))
        return NS(symbol=sym, shortable=bool(ok[0]), easy_to_borrow=bool(ok[1]), attributes=[])

    def get_orders(self, req=None):
        self.advance()
        st = _v(getattr(req, "status", "open") or "open")
        syms = getattr(req, "symbols", None)
        until = getattr(req, "until", None)
        out = [o for o in self.orders if not syms or o.symbol in syms]
        if until is not None:
            u = pd.Timestamp(until)
            u = u.tz_localize("UTC") if u.tzinfo is None else u
            out = [o for o in out if pd.Timestamp(o.submitted_at) < u]
        if st == "closed":
            out = [o for o in out if o.status not in OPEN]
        elif st == "open":
            out = [o for o in out if o.status in OPEN or any(leg.status in OPEN for leg in o.legs or [])]
        return sorted(out, key=lambda o: o.submitted_at, reverse=True)

    def get_order_by_id(self, oid):
        return self.by_id[str(oid)]

    def get_all_positions(self):
        self.advance()
        k = self.mkt.minute(self.clock.now)
        out = []
        for s, q in self.pos.items():
            px = self.mkt.last_close(s, k) or self.avg.get(s, 0.0)
            avail = abs(q) - self._reserved(s)
            out.append(NS(symbol=s, qty=str(q), qty_available=str(np.sign(q) * max(0.0, avail)),
                          current_price=str(px), avg_entry_price=str(self.avg.get(s, 0.0)),
                          unrealized_pl=str((px - self.avg.get(s, 0.0)) * q), side="long" if q > 0 else "short",
                          market_value=str(px * q)))
        return out

    def cancel_order_by_id(self, oid):
        o = self.by_id.get(str(oid))
        if o is None:
            raise RuntimeError("order not found")
        if o.status not in OPEN:
            raise RuntimeError(f"order is not cancelable (status {o.status})")
        t = self._now_utc()
        o.status, o.canceled_at = "canceled", t
        for leg in o.legs or []:
            if leg.status in OPEN:
                leg.status, leg.canceled_at = "canceled", t

    def cancel_orders(self):
        for o in list(self._all()):
            if o.status in OPEN:
                o.status, o.canceled_at = "canceled", self._now_utc()

    def replace_order_by_id(self, oid, req):
        o = self.by_id.get(str(oid))
        if o is None or o.status not in OPEN:
            raise RuntimeError("order is not replaceable")
        if getattr(req, "stop_price", None) is not None:
            o.stop_price = float(req.stop_price)
        if getattr(req, "limit_price", None) is not None:
            o.limit_price = float(req.limit_price)
        return o

    def _market_now(self, o):
        """A market order fills at the open of the bar of the current minute (or waits for the symbol's next bar)."""
        k = max(self.mkt.minute(self.clock.now), self.done_min + 1)
        o._active = k
        bar = self.mkt.bar(o.symbol, k)
        if bar is not None and k < 390:
            self._fill(o, float(bar[0]), k, "market")

    def close_position(self, sym):
        q = self.pos.get(sym)
        if not q:
            raise RuntimeError(f"position does not exist: {sym}")
        if abs(q) - self._reserved(sym) < abs(q) - 1e-9:
            raise RuntimeError("insufficient qty available for order (shares held for orders)")
        o = self._new(client_order_id=f"close-{next(self._ids)}", symbol=sym, side="sell" if q > 0 else "buy",
                      qty=str(abs(q)), order_type="market", _role="exit")
        self.orders.append(o)
        self._market_now(o)
        return o

    def close_all_positions(self, cancel_orders=True):
        if cancel_orders:
            self.cancel_orders()
        return [self.close_position(s) for s in list(self.pos)]

    def submit_order(self, req):
        coid = getattr(req, "client_order_id", None)
        if coid and any(o.client_order_id == coid for o in self._all()):
            raise RuntimeError('{"code":40010001,"message":"client_order_id must be unique"}')
        sym, qty = req.symbol, abs(float(req.qty))
        side = _v(req.side)
        oc = _v(getattr(req, "order_class", None) or "simple")
        t = "market" if req.__class__.__name__.startswith("Market") else (
            "limit" if req.__class__.__name__.startswith("Limit") else "stop")
        if qty <= 0:
            raise RuntimeError("qty must be > 0")
        opening = oc in ("bracket", "oto")                       # MCF entries are brackets / OTO; the rest are exits
        o = self._new(client_order_id=coid, symbol=sym, side=side, qty=str(qty), order_type=t, order_class=oc,
                      stop_price=getattr(req, "stop_price", None), limit_price=getattr(req, "limit_price", None),
                      extended_hours=bool(getattr(req, "extended_hours", False)),
                      _role="entry" if opening else ("oco" if oc == "oco" else "exit"))
        opp = "sell" if side == "buy" else "buy"
        legs = []
        if opening:
            sl = getattr(req, "stop_loss", None)
            tp = getattr(req, "take_profit", None)
            if tp is not None:
                legs.append(self._new(client_order_id=f"leg-{next(self._ids)}", symbol=sym, side=opp, qty=str(qty),
                                      order_type="limit", limit_price=float(tp.limit_price), status="new",
                                      order_class=oc, _role="target", _parent=o))
            if sl is not None:
                legs.append(self._new(client_order_id=f"leg-{next(self._ids)}", symbol=sym, side=opp, qty=str(qty),
                                      order_type="stop", stop_price=float(sl.stop_price), status="held",
                                      order_class=oc, _role="stop", _parent=o))
        elif oc == "oco":                                          # limit target parent + stop-loss leg (protection)
            sl = getattr(req, "stop_loss", None)
            tp = getattr(req, "take_profit", None)
            if tp is not None:
                o.limit_price = float(tp.limit_price)
            legs.append(self._new(client_order_id=f"leg-{next(self._ids)}", symbol=sym, side=side, qty=str(qty),
                                  order_type="stop", stop_price=float(sl.stop_price), status="held", order_class=oc,
                                  _role="ocoleg", _parent=o))
        o.legs = legs or None
        self.orders.append(o)
        if t == "market":
            self._market_now(o)
        else:
            k = max(self.mkt.minute(self.clock.now), self.done_min + 1)
            o._active = k
            for leg in legs:
                leg._active = k
        return o


class SimDataClient:
    """StockHistoricalDataClient stand-in for the runner's quote checks: the latest quote is the last completed bar's
    close +- half a spread (spread = max(1 cent, spread_bps of the price)), stamped one second before the poll."""

    def __init__(self, clock: SimClock, market: SimMarket, spread_bps: float = 2.0):
        self.clock, self.mkt, self.spread_bps = clock, market, float(spread_bps)

    def get_stock_latest_quote(self, req):
        syms = req.symbol_or_symbols
        syms = [syms] if isinstance(syms, str) else list(syms)
        k = self.mkt.minute(self.clock.now)
        out = {}
        for s in syms:
            px = self.mkt.last_close(s, k)
            if px is None:
                raise KeyError(s)
            half = max(0.005, px * self.spread_bps / 2e4)
            out[s] = NS(bid_price=round(px - half, 4), ask_price=round(px + half, 4),
                        timestamp=(self.clock.now - timedelta(seconds=1)).tz_convert("UTC").to_pydatetime())
        return out

    def get_stock_bars(self, req):
        raise RuntimeError("replay: bars come from the replay feed, not the data client")
