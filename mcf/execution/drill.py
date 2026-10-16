"""Outage fire drills (owner 2026-10-16, outage plan step 6). Each scenario runs the real protection code against a fake
Alpaca account and a synthetic clock and asserts that the protections fire, in order, and only on MCF's own orders:

  stale_data  - SIP bars stop: entries pause -> after protect_min the stop of the lot in profit moves to breakeven (the
                losing lot is left alone) -> after flatten_min every MCF position is flattened. No action while fresh.
  broker_down - the broker clock call fails: after flatten_min the runner flattens (partial outage: orders still go
                through); a full outage defers the flatten until the broker answers again.
  run_dead    - the watchdog: status.json 20 min old with MCF positions open -> dry mode only reports; act mode cancels
                and flattens the mcf- book while a long-hold mcl- order and a non-MCF position stay untouched; a fresh
                status -> no action; data stale longer than flatten_min -> flatten.

    python -m mcf.execution.drill --scenario stale_data|broker_down|run_dead|all

Also run by pytest (tests/test_outage.py). No network, no orders, no emails. Educational only - not financial advice."""

from __future__ import annotations

import argparse
import itertools
import tempfile
import time as _real_time
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace as NS

import pandas as pd

NY = "America/New_York"
DAY = "2026-10-13"
OPEN = {"new", "held", "accepted", "pending_new", "partially_filled"}
_ids = itertools.count(1)


def _v(x):
    return str(getattr(x, "value", x)).lower()


class DrillAlpaca:
    """A small stand-in for alpaca TradingClient: bracket parents with nested legs, netted positions, cancels, stop
    replaces, market closes. `down` = every call fails; `clock_down` = only the clock call fails (partial outage)."""

    def __init__(self, now: pd.Timestamp):
        self.orders, self.pos, self.price = [], {}, {}
        self.now = now.tz_convert("UTC").to_pydatetime()
        self.down = self.clock_down = False
        self.cancelled, self.replaced, self.closed = [], [], []

    def _chk(self):
        if self.down:
            raise ConnectionError("broker API unreachable (drill)")

    # -- drill helpers
    def add_lot(self, coid, symbol, side, qty, entry, stop, target):
        s = "buy" if side == 1 else "sell"
        opp = "sell" if side == 1 else "buy"
        legs = [NS(id=f"leg-{next(_ids)}", client_order_id=f"uuid-{next(_ids)}", symbol=symbol, side=opp,
                   order_type="stop", stop_price=stop, limit_price=None, status="held", filled_qty="0",
                   filled_avg_price=None, legs=None),
                NS(id=f"leg-{next(_ids)}", client_order_id=f"uuid-{next(_ids)}", symbol=symbol, side=opp,
                   order_type="limit", stop_price=None, limit_price=target, status="new", filled_qty="0",
                   filled_avg_price=None, legs=None)]
        self.orders.append(NS(id=f"ord-{next(_ids)}", client_order_id=coid, symbol=symbol, side=s, qty=str(qty),
                              filled_qty=str(qty), filled_avg_price=str(entry), status="filled", order_type="market",
                              submitted_at=self.now, legs=legs))
        self.pos[symbol] = self.pos.get(symbol, 0.0) + side * qty

    def add_order(self, coid, symbol, side="buy", qty=1, status="new"):
        self.orders.append(NS(id=f"ord-{next(_ids)}", client_order_id=coid, symbol=symbol, side=side, qty=str(qty),
                              filled_qty="0", filled_avg_price=None, status=status, order_type="limit",
                              submitted_at=self.now, legs=None))

    def _all(self):
        for o in self.orders:
            yield o
            yield from o.legs or []

    def _reserved(self, sym):
        return sum(float(o.filled_qty) for o in self.orders
                   if o.symbol == sym and o.legs and any(leg.status in OPEN for leg in o.legs))

    # -- TradingClient surface
    def get_account(self):
        self._chk()
        return NS(equity="100000", cash="100000")

    def get_clock(self):
        self._chk()
        if self.clock_down:
            raise ConnectionError("clock endpoint unreachable (drill)")
        return NS(is_open=True, timestamp=self.now, next_open=self.now)

    def get_asset(self, sym):
        return NS(shortable=True, easy_to_borrow=True)

    def get_orders(self, req):
        self._chk()
        st = _v(req.status)
        syms = getattr(req, "symbols", None)
        out = [o for o in self.orders if not syms or o.symbol in syms]
        if st == "closed":
            out = [o for o in out if o.status not in OPEN]
        elif st == "open":
            out = [o for o in out if o.status in OPEN]
        return out

    def get_all_positions(self):
        self._chk()
        return [NS(symbol=s, qty=str(q), qty_available=str((abs(q) - self._reserved(s)) * (1 if q > 0 else -1)),
                   current_price=str(self.price.get(s, 0)), avg_entry_price="0", unrealized_pl="0")
                for s, q in self.pos.items()]

    def cancel_order_by_id(self, oid):
        self._chk()
        o = next(x for x in self._all() if x.id == oid)
        if o.status not in OPEN:
            raise RuntimeError("order is not cancelable")
        o.status = "canceled"
        self.cancelled.append(o.client_order_id)
        for leg in o.legs or []:
            if leg.status in OPEN:
                leg.status = "canceled"

    def replace_order_by_id(self, oid, req):
        self._chk()
        leg = next(x for x in self._all() if x.id == oid)
        leg.stop_price = req.stop_price
        self.replaced.append((oid, req.stop_price))

    def close_position(self, sym):
        self._chk()
        self.closed.append(sym)
        self.pos.pop(sym, None)

    def submit_order(self, req):
        self._chk()
        raise RuntimeError("drill: no new orders expected")


@contextmanager
def _no_sleep():
    from . import runner as R

    orig = R._time.sleep
    R._time.sleep = lambda s: None
    try:
        yield
    finally:
        R._time.sleep = orig


def _runner(tmp: str, client: DrillAlpaca, live: dict | None = None):
    from ..config import load_config
    from . import runner as R
    from .alpaca_broker import AlpacaBroker

    cfg = load_config()
    cfg["data"]["journal_path"] = str(Path(tmp) / "drill.db")
    cfg["live"].update(live or {})
    b = AlpacaBroker.__new__(AlpacaBroker)
    b.client = client
    r = R.PaperRunner(cfg, [], {}, broker=b)
    r._contexts = lambda bars, today: []              # no setups: the drill is about protection, not entries
    return r


def _book(c: DrillAlpaca, prefix="mcf-"):
    """Two MCF lots (XYZ long in profit, ABC long under water), a long-hold mcl- order and a non-MCF position."""
    c.add_lot(f"{prefix}A-XYZ-20261013-1000", "XYZ", 1, 100, 10.00, 9.00, 12.00)
    c.add_lot(f"{prefix}B-ABC-20261013-1001", "ABC", 1, 50, 20.00, 19.00, 23.00)
    c.price.update(XYZ=10.50, ABC=19.60, OTHER=50.0)
    c.add_order("mcl-S6-20261013-SPY-b", "SPY")
    c.pos["OTHER"] = 10.0


def _bars(last: pd.Timestamp, syms=("XYZ", "ABC", "DEF")):
    idx = pd.date_range(pd.Timestamp(f"{DAY} 09:30", tz=NY), last, freq="1min")
    b = pd.DataFrame({"open": 10.0, "high": 10.1, "low": 9.9, "close": 10.0, "volume": 1e5}, index=idx)
    return {s: b for s in syms}


def _stop(c, coid):
    o = next(o for o in c.orders if o.client_order_id == coid)
    return next(float(leg.stop_price) for leg in o.legs if leg.order_type == "stop")


def _check(cond, msg, log):
    log.append(("PASS " if cond else "FAIL ") + msg)
    if not cond:
        raise AssertionError(msg)


def drill_stale_data(log: list) -> dict:
    with tempfile.TemporaryDirectory() as tmp, _no_sleep():
        t0 = pd.Timestamp(f"{DAY} 10:00:05", tz=NY)
        c = DrillAlpaca(t0)
        _book(c)
        r = _runner(tmp, c)
        frozen = pd.Timestamp(f"{DAY} 10:00", tz=NY)
        for m in range(0, 11):                         # normal operation first: fresh bars every minute
            now = pd.Timestamp(f"{DAY} 09:50:05", tz=NY) + pd.Timedelta(minutes=m)
            r.fetch = lambda now, _b=_bars(now.floor("1min") - pd.Timedelta(minutes=1)): _b
            r.step(now)
        _check(r.health["outage_actions"] == [] and r.health["data_stale"] is None,
               "fresh data: no outage action, not stale", log)
        times = {}
        for m in range(1, 50):                         # SIP bars stop at 10:00
            now = frozen + pd.Timedelta(minutes=m, seconds=5)
            r.fetch = lambda now, _b=_bars(frozen): _b
            r.step(now)
            for a in r.health["outage_actions"]:
                times.setdefault(a["action"], (now, a))
        acts = [a["action"] for a in r.health["outage_actions"]]
        _check(acts == ["pause", "protect", "flatten"], f"actions in order pause -> protect -> flatten ({acts})", log)
        since = pd.Timestamp(r.health["data_stale"]["since"])
        _check(times["pause"][0] == since, f"pause when data went stale ({since:%H:%M:%S})", log)
        dp = (times["protect"][0] - since).total_seconds() / 60
        df = (times["flatten"][0] - since).total_seconds() / 60
        _check(15 <= dp < 16, f"protect after {dp:.0f} min of continuous staleness (protect_min 15)", log)
        _check(30 <= df < 31, f"flatten after {df:.0f} min (flatten_min 30)", log)
        moved = times["protect"][1]["moved"]
        _check(moved == ["XYZ mcf-A-XYZ-20261013-1000 -> 10.0"] and times["protect"][1]["not_in_profit"] == 1,
               "breakeven only for the lot in profit (XYZ 9.00 -> 10.00; ABC left at 19.00)", log)
        _check(set(c.pos) == {"OTHER"} and sorted(c.closed) == ["ABC", "XYZ"], "flatten closed XYZ and ABC only", log)
        _check(not any(x.startswith("mcl-") for x in c.cancelled), "long-hold mcl- order untouched", log)
        return {"actions": r.health["outage_actions"]}


def drill_broker_down(log: list) -> dict:
    with tempfile.TemporaryDirectory() as tmp, _no_sleep():
        t0 = pd.Timestamp(f"{DAY} 11:00:05", tz=NY)
        # (a) partial outage: the clock endpoint fails, orders still work -> flatten at flatten_min
        c = DrillAlpaca(t0)
        _book(c)
        r = _runner(tmp, c)
        c.clock_down = True
        err = ConnectionError("clock endpoint unreachable (drill)")
        for m in range(0, 29):
            r._broker_unreachable(t0 + pd.Timedelta(minutes=m), err)
        _check([a["action"] for a in r.health["outage_actions"]] == ["broker_unreachable"] and len(c.pos) == 3,
               "broker unreachable < 30 min: logged, nothing flattened", log)
        r._broker_unreachable(t0 + pd.Timedelta(minutes=30), err)
        _check(r.health["outage_actions"][-1]["action"] == "flatten" and set(c.pos) == {"OTHER"},
               "broker unreachable 30 min: MCF positions flattened, OTHER untouched", log)
        r._broker_unreachable(t0 + pd.Timedelta(minutes=31), err)
        _check(sum(a["action"] == "flatten" for a in r.health["outage_actions"]) == 1, "flatten once per outage", log)
        r._broker_reachable(t0 + pd.Timedelta(minutes=32))
        _check(r.health["outage_actions"][-1]["action"] == "broker_restored", "recovery logged", log)
        # (b) full outage: the flatten fails while down and goes through as soon as the broker answers
        c2 = DrillAlpaca(t0)
        _book(c2)
        r2 = _runner(tmp, c2)
        c2.down = True
        for m in range(0, 36):
            r2._broker_unreachable(t0 + pd.Timedelta(minutes=m), err)
        acts = [a["action"] for a in r2.health["outage_actions"]]
        _check(acts.count("flatten_failed") == 1 and len(c2.pos) == 3,
               "full outage: flatten attempted every poll from 30 min, failure logged once", log)
        c2.down = False
        r2._broker_reachable(t0 + pd.Timedelta(minutes=36))
        acts = [a["action"] for a in r2.health["outage_actions"]]
        _check(acts[-2:] == ["broker_restored", "flatten"] and set(c2.pos) == {"OTHER"},
               "broker back after 36 min: deferred flatten done", log)
        # (c) a short blip never flattens
        c3 = DrillAlpaca(t0)
        _book(c3)
        r3 = _runner(tmp, c3)
        r3._broker_unreachable(t0, err)
        r3._broker_reachable(t0 + pd.Timedelta(minutes=3))
        _check(len(c3.pos) == 3 and c3.closed == [], "3-minute blip: nothing flattened", log)
        return {"actions": r.health["outage_actions"] + r2.health["outage_actions"]}


def drill_run_dead(log: list) -> dict:
    from .alpaca_broker import AlpacaBroker
    from .watchdog import run as watchdog_run

    live = {"outage": {"enabled": True, "flatten_min": 30, "watchdog_dead_min": 15}}
    now = pd.Timestamp(f"{DAY} 12:00:00", tz=NY)

    def account():
        c = DrillAlpaca(now)
        _book(c)
        b = AlpacaBroker.__new__(AlpacaBroker)
        b.client = c
        return c, b

    fresh = {"asof": (now - pd.Timedelta(minutes=2)).tz_convert("UTC").isoformat(), "phase": "trading",
             "health": {"data_stale": None}}
    dead = {**fresh, "asof": (now - pd.Timedelta(minutes=20)).tz_convert("UTC").isoformat()}
    stale = {**fresh, "health": {"data_stale": {"since": str(now - pd.Timedelta(minutes=35))}}}
    out = {}
    c, b = account()
    d = watchdog_run(fresh, b, "mcf-", live, "act", now=now, sleep=lambda s: None)
    _check(d["action"] == "none" and len(c.pos) == 3, "fresh status: no action", log)
    c, b = account()
    d = out["dry"] = watchdog_run(dead, b, "mcf-", live, "dry", now=now, sleep=lambda s: None)
    _check(d["action"] == "flatten" and not d["done"] and len(c.pos) == 3 and c.cancelled == [],
           "status 20 min old, dry mode: reports 'would flatten', touches nothing", log)
    c, b = account()
    d = out["act"] = watchdog_run(dead, b, "mcf-", live, "act", now=now, sleep=lambda s: None)
    _check(d["done"] and d["left"] == [] and set(c.pos) == {"OTHER"}, "status 20 min old, act: MCF book flattened", log)
    _check(c.cancelled and not any(x.startswith("mcl-") for x in c.cancelled) and
           next(o for o in c.orders if o.client_order_id.startswith("mcl-")).status == "new",
           "only mcf- orders cancelled; mcl- order still working", log)
    c, b = account()
    d = watchdog_run(stale, b, "mcf-", live, "act", now=now, sleep=lambda s: None)
    _check(d["action"] == "flatten" and set(c.pos) == {"OTHER"}, "data stale 35 min (> flatten_min): flattened", log)
    c, b = account()
    c.pos.pop("XYZ"), c.pos.pop("ABC")
    for o in c.orders:
        for leg in o.legs or []:
            leg.status = "filled" if leg.order_type == "stop" else "canceled"
    d = watchdog_run(dead, b, "mcf-", live, "act", now=now, sleep=lambda s: None)
    _check(d["action"] == "none", "run dead but no MCF exposure: no action", log)
    _check(watchdog_run(dead, b, "mcf-", live, "act", now=pd.Timestamp(f"{DAY} 16:10", tz=NY))["action"] == "none",
           "outside the session: no action", log)
    try:
        watchdog_run(dead, b, "mcl-", live, "act", now=now)
        ok = False
    except ValueError:
        ok = True
    _check(ok, "watchdog refuses a non-MCF prefix (mcl-)", log)
    return out


SCENARIOS = {"stale_data": drill_stale_data, "broker_down": drill_broker_down, "run_dead": drill_run_dead}


def run_scenario(name: str) -> list[str]:
    log: list[str] = []
    SCENARIOS[name](log)
    return log


def main(argv=None):
    ap = argparse.ArgumentParser(description="MCF outage fire drills (fake broker, synthetic clock)")
    ap.add_argument("--scenario", default="all", choices=[*SCENARIOS, "all"])
    a = ap.parse_args(argv)
    failed = False
    for name in SCENARIOS if a.scenario == "all" else [a.scenario]:
        t = _real_time.time()
        log: list[str] = []
        try:
            SCENARIOS[name](log)
            ok = True
        except AssertionError:
            ok, failed = False, True
        print(f"== drill {name}: {'PASSED' if ok else 'FAILED'} ({_real_time.time() - t:.1f}s)")
        for line in log:
            print("   " + line)
    print("Educational only - not financial advice.")
    raise SystemExit(1 if failed else 0)


if __name__ == "__main__":
    main()
