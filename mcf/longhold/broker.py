"""Alpaca adapter for the long-hold (S6) paper account. Orders go ONLY to ALPACA_TRADE_API_KEY /
ALPACA_TRADE_SECRET_KEY (the dedicated long-hold paper account; the workflow maps ALPACA_LONGHOLD_* onto them); there
is deliberately no fallback to the primary keys. Paper endpoint only. Only orders with the `mcl-` prefix are listed
or touched. Educational only - not financial advice."""
from __future__ import annotations

import os

from .core import PREFIX

KEY_ENVS_FORBIDDEN = ("ALPACA_API_KEY", "ALPACA_TESTING_API_KEY", "ALPACA_TESTING2_API_KEY", "ALPACA_PRIMARY_API_KEY")


class KeySeparationError(RuntimeError):
    pass


def check_key_separation(env=None) -> str:
    """The long-hold book must run on its own account (DESIGN.md 2). Refuse when the trade key is missing or equals
    the primary / Testing / Testing-2 key. Never prints a key."""
    env = os.environ if env is None else env
    trade = (env.get("ALPACA_TRADE_API_KEY") or "").strip()
    if not trade:
        raise KeySeparationError("ALPACA_TRADE_API_KEY is not set (map ALPACA_LONGHOLD_API_KEY onto it)")
    if not (env.get("ALPACA_TRADE_SECRET_KEY") or "").strip():
        raise KeySeparationError("ALPACA_TRADE_SECRET_KEY is not set")
    for name in KEY_ENVS_FORBIDDEN:
        other = (env.get(name) or "").strip()
        if other and other == trade:
            raise KeySeparationError(f"ALPACA_TRADE_API_KEY equals {name}: the long-hold book needs its own account")
    return "ok"


def _v(x):
    return str(getattr(x, "value", x)).lower() if x is not None else None


def _f(x):
    return None if x is None else float(x)


class AlpacaLongholdBroker:
    def __init__(self, env=None):
        from alpaca.trading.client import TradingClient

        env = os.environ if env is None else env
        check_key_separation(env)
        self.client = TradingClient(env["ALPACA_TRADE_API_KEY"], env["ALPACA_TRADE_SECRET_KEY"], paper=True)

    def account(self) -> dict:
        a = self.client.get_account()
        return {"equity": float(a.equity), "cash": float(a.cash), "last_equity": float(a.last_equity or a.equity),
                "status": _v(a.status), "trading_blocked": bool(a.trading_blocked),
                "buying_power": float(a.buying_power)}

    def positions(self) -> dict[str, dict]:
        return {p.symbol: {"qty": float(p.qty), "market_value": float(p.market_value),
                           "avg_entry_price": float(p.avg_entry_price), "current_price": _f(p.current_price),
                           "lastday_price": _f(p.lastday_price), "unrealized_pl": _f(p.unrealized_pl)}
                for p in self.client.get_all_positions()}

    def calendar(self, start, end) -> list:
        from alpaca.trading.requests import GetCalendarRequest

        return [c.date for c in self.client.get_calendar(GetCalendarRequest(start=start, end=end))]

    def clock(self) -> dict:
        c = self.client.get_clock()
        return {"is_open": bool(c.is_open), "next_open": str(c.next_open), "next_close": str(c.next_close)}

    def tradable(self, symbol: str) -> bool:
        a = self.client.get_asset(symbol)
        return bool(a.tradable) and _v(a.status) == "active"

    def orders(self, prefix: str, after) -> list[dict]:
        """This book's orders (client id starting with `prefix`, itself starting with mcl-) submitted after `after`."""
        from alpaca.trading.enums import QueryOrderStatus
        from alpaca.trading.requests import GetOrdersRequest

        assert prefix.startswith(PREFIX)
        out = self.client.get_orders(GetOrdersRequest(status=QueryOrderStatus.ALL, after=after, limit=500))
        return [{"client_order_id": o.client_order_id, "symbol": o.symbol, "side": _v(o.side), "qty": _f(o.qty),
                 "status": _v(o.status), "filled_qty": _f(o.filled_qty), "filled_avg_price": _f(o.filled_avg_price),
                 "time_in_force": _v(o.time_in_force), "submitted_at": str(o.submitted_at)}
                for o in out if (o.client_order_id or "").startswith(prefix)]

    def submit(self, symbol: str, qty: int, side: str, tif: str, client_order_id: str) -> dict:
        """Whole-share market order; tif 'opg' (market-on-open), 'cls' (market-on-close) or 'day'."""
        from alpaca.trading.enums import OrderSide, TimeInForce
        from alpaca.trading.requests import MarketOrderRequest

        assert client_order_id.startswith(PREFIX) and qty >= 1 and float(qty).is_integer()
        o = self.client.submit_order(MarketOrderRequest(
            symbol=symbol, qty=int(qty), side=OrderSide.BUY if side == "buy" else OrderSide.SELL,
            time_in_force={"opg": TimeInForce.OPG, "cls": TimeInForce.CLS, "day": TimeInForce.DAY}[tif],
            client_order_id=client_order_id))
        return {"client_order_id": o.client_order_id, "status": _v(o.status), "id": str(o.id)}


class CalendarOnly:
    """Dry-run helper: the exchange calendar through the primary (data) keys, GET /v2/calendar only."""

    def __init__(self, env=None):
        from alpaca.trading.client import TradingClient

        env = os.environ if env is None else env
        self.client = TradingClient(env["ALPACA_API_KEY"], env["ALPACA_SECRET_KEY"], paper=True)

    calendar = AlpacaLongholdBroker.calendar
