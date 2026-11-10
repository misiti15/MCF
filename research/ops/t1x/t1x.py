"""T1X (owner "T1X yes", 2026-11-09): find and close the position in the Testing 1 paper account that MCF never placed.

  python research/ops/t1x/t1x.py inspect <journal.db>                 # READ-ONLY: positions, journal, activities
  python research/ops/t1x/t1x.py close <journal.db> <SYMBOL> <QTY> [TIF] [COID_DATE]   # one market close (default opg)

`close` refuses unless: the journal has no open MCF order, the account holds SYMBOL with exactly QTY (signed: negative =
short), QTY is a whole number, and no open order exists for SYMBOL. The order's client_order_id starts "owner-t1x-" so
MCF's reconcile never takes it for an MCF lot. Prints no keys, no account number. Educational only - not financial advice.
"""
import os
import sqlite3
import sys

import requests

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))
BASE = "https://paper-api.alpaca.markets/v2"
ACT_DAYS = ["2026-11-04", "2026-11-05", "2026-11-06", "2026-11-07", "2026-11-08", "2026-11-09", "2026-11-10"]
DIAG_ORDER = "d2db7df7-6a04-432c-802d-c2ca88dc23bb"  # 11-09 opg buy-to-cover SOXX 12 that did not fill
DIAG_SYMBOL = "SOXX"
DIAG_SINCE = "2026-11-04"
ORDER_KEYS = ("id", "client_order_id", "symbol", "side", "qty", "filled_qty", "filled_avg_price", "type", "time_in_force",
              "status", "created_at", "submitted_at", "updated_at", "filled_at", "canceled_at", "expired_at", "failed_at",
              "replaced_at", "extended_hours", "position_intent", "order_class", "reject_reason", "status_reason", "reason")
TIFS = ("opg", "day")


def _h():
    return {"APCA-API-KEY-ID": os.environ["ALPACA_TRADE_API_KEY"], "APCA-API-SECRET-KEY": os.environ["ALPACA_TRADE_SECRET_KEY"]}


def _get(path, **params):
    r = requests.get(f"{BASE}{path}", headers=_h(), params=params, timeout=30)
    r.raise_for_status()
    return r.json()


def activities(day):
    out, token = [], None
    while True:
        p = {"date": day, "direction": "asc", "page_size": 100}
        if token:
            p["page_token"] = token
        got = _get("/account/activities", **p)
        out += got
        if len(got) < 100:
            return out
        token = got[-1]["id"]


def journal_open(db):
    con = sqlite3.connect(db)
    n = con.execute("select count(*) from orders where status not in ('closed','rejected','expired')").fetchone()[0]
    last = con.execute("select max(date) from trades").fetchone()[0]
    return n, last


def positions():
    return _get("/positions")


def show_positions(pos):
    print(f"positions: {len(pos)}")
    for p in pos:
        print({k: p.get(k) for k in ("symbol", "asset_id", "side", "qty", "qty_available", "avg_entry_price", "cost_basis", "market_value",
                                     "current_price", "unrealized_pl", "asset_class")})


def inspect(db):
    print("# T1X inspect (read-only)\n\nEducational only - not financial advice.\n")
    n, last = journal_open(db)
    print(f"journal: open MCF orders {n}, last trade date {last}")
    a = _get("/account")
    print({k: a.get(k) for k in ("status", "equity", "cash", "long_market_value", "short_market_value", "last_equity")})
    pos = positions()
    show_positions(pos)
    syms = {p["symbol"] for p in pos}
    print("open orders:", [(o["symbol"], o["side"], o["qty"], o["type"], o["client_order_id"][:12])
                           for o in _get("/orders", status="open", limit=500)])
    for day in ACT_DAYS:
        acts = activities(day)
        non_fill = [x for x in acts if x.get("activity_type") != "FILL"]
        sym_fills = [x for x in acts if x.get("activity_type") == "FILL" and x.get("symbol") in syms]
        print(f"\n## {day}: {len(acts)} activities, {len(non_fill)} non-fill, {len(sym_fills)} fills in held symbols")
        for x in non_fill:
            print({k: x.get(k) for k in ("id", "activity_type", "date", "symbol", "qty", "price", "per_share_amount",
                                         "net_amount", "cusip", "description", "status")})
        for x in sym_fills:
            print({k: x.get(k) for k in ("id", "transaction_time", "symbol", "side", "qty", "price", "order_id",
                                         "cum_qty", "leaves_qty")})
    for s in sorted(syms):
        try:
            print(f"\nasset {s}:", {k: v for k, v in _get(f"/assets/{s}").items()
                                     if k in ("id", "symbol", "name", "exchange", "status", "tradable", "shortable")})
        except requests.HTTPError as e:
            print(f"asset {s}: {e}")
    diagnose()


def diagnose():
    """GET-only: why the 11-09 opg close of the phantom SOXX short did not fill."""
    print(f"\n# diagnosis {DIAG_SYMBOL}")
    try:
        o = _get(f"/orders/{DIAG_ORDER}")
        print("order:", {k: o.get(k) for k in ORDER_KEYS if k in o})
        extra = {k: v for k, v in o.items() if k not in ORDER_KEYS and k not in ("legs", "asset_id", "asset_class")
                 and v not in (None, "", [], False)}
        print("order other fields:", extra)
    except requests.HTTPError as e:
        print(f"order {DIAG_ORDER}: {e}")
    try:
        p = _get(f"/positions/{DIAG_SYMBOL}")
        print("position:", {k: p.get(k) for k in ("symbol", "asset_id", "side", "qty", "qty_available", "avg_entry_price",
                                                  "cost_basis", "current_price", "exchange")})
    except requests.HTTPError as e:
        print(f"position {DIAG_SYMBOL}: {e}")
    try:
        a = _get(f"/assets/{DIAG_SYMBOL}")
        print("asset:", {k: a.get(k) for k in ("id", "symbol", "status", "exchange", "tradable", "shortable",
                                               "easy_to_borrow", "fractionable", "marginable", "attributes")})
    except requests.HTTPError as e:
        print(f"asset {DIAG_SYMBOL}: {e}")
    print("orders for symbol (all, last 20):", [{k: x.get(k) for k in ("id", "client_order_id", "side", "qty", "type",
                                                 "time_in_force", "status", "created_at", "filled_avg_price")}
                                                for x in _get("/orders", status="all", limit=20, symbols=DIAG_SYMBOL)])
    try:
        nt = _get("/account/activities", category="non_trade_activity", after=DIAG_SINCE, direction="asc", page_size=100)
    except requests.HTTPError as e:
        print(f"non-trade activities: {e}")
        nt = []
    mine = [x for x in nt if x.get("symbol") == DIAG_SYMBOL]
    print(f"non-trade activities since {DIAG_SINCE}: {len(nt)} total, {len(mine)} for {DIAG_SYMBOL}")
    for x in mine:
        print({k: v for k, v in x.items() if k not in ("account_id",)})


def close(db, symbol, qty, tif="opg", coid_date="20261109"):
    from alpaca.trading.enums import OrderSide, TimeInForce
    from alpaca.trading.requests import MarketOrderRequest

    from mcf.execution.alpaca_broker import AlpacaBroker

    q = float(qty)
    n, _ = journal_open(db)
    if n:
        sys.exit(f"REFUSED: journal has {n} open MCF orders")
    pos = {p["symbol"]: p for p in positions()}
    p = pos.get(symbol)
    if p is None:
        sys.exit(f"REFUSED: no {symbol} position")
    held = float(p["qty"])
    if held != q:
        sys.exit(f"REFUSED: {symbol} qty {held} != expected {q}")
    if q != int(q) or q == 0:
        sys.exit(f"REFUSED: qty {q} is not a whole, non-zero number (opg needs whole shares)")
    if tif not in TIFS:
        sys.exit(f"REFUSED: tif {tif} not in {TIFS}")
    if not (coid_date.isdigit() and len(coid_date) == 8):
        sys.exit(f"REFUSED: coid date {coid_date} is not YYYYMMDD")
    if [o for o in _get("/orders", status="open", limit=500, symbols=symbol)]:
        sys.exit(f"REFUSED: open order(s) already exist for {symbol}")
    side = OrderSide.BUY if q < 0 else OrderSide.SELL
    coid = f"owner-t1x-{symbol}-{coid_date}"
    b = AlpacaBroker(paper=True)
    o = b.client.submit_order(MarketOrderRequest(symbol=symbol, qty=abs(int(q)), side=side,
                                                 time_in_force=TimeInForce(tif), client_order_id=coid))
    print({"order_id": str(o.id), "client_order_id": o.client_order_id, "symbol": o.symbol, "side": str(o.side),
           "qty": str(o.qty), "type": str(o.type), "time_in_force": str(o.time_in_force), "status": str(o.status)})


if __name__ == "__main__":
    if sys.argv[1] == "inspect":
        inspect(sys.argv[2])
    elif sys.argv[1] == "close":
        close(*sys.argv[2:7])
    else:
        sys.exit("usage: inspect <db> | close <db> <SYMBOL> <QTY> [opg|day] [YYYYMMDD]")
