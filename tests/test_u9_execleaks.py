"""U9 execution leaks (research/usage/u9_execleaks): U9-ETB bulk borrow list + once-per-day ETB journaling for short-only
setups, and U9-TGT quote pre-check (target / stop already passed at the quote). Proposal patch; educational only - not
financial advice."""
from types import SimpleNamespace as NS

import pandas as pd

import mcf.execution.runner as R
from mcf.config import load_config
from mcf.execution.alpaca_broker import AlpacaBroker
from mcf.strategies.base import Signal
from tests.test_outage import NOW, _xc_runner


# ---------------------------------------------------------------- broker: bulk list
class _Client:
    def __init__(self, rows=None, exc=None):
        self.rows, self.exc, self.calls = rows or [], exc, []

    def get(self, path, data=None):
        self.calls.append((path, data))
        if self.exc:
            raise self.exc
        return self.rows

    def get_asset(self, symbol):
        self.calls.append(("get_asset", symbol))
        return NS(shortable=True, easy_to_borrow=True)


def _broker(c):
    b = object.__new__(AlpacaBroker)
    b.client = c
    return b


def test_load_borrow_fills_cache_one_call():
    c = _Client([{"symbol": "AAPL", "shortable": True, "easy_to_borrow": True},
                 {"symbol": "SOXS", "shortable": True, "easy_to_borrow": False},
                 {"symbol": "UVIX", "shortable": False, "easy_to_borrow": False}])
    b = _broker(c)
    assert b.borrow_known("AAPL") is None
    assert b.load_borrow() == 3
    assert c.calls == [("/assets", {"status": "active", "asset_class": "us_equity"})]
    assert (b.can_short("AAPL"), b.can_short("SOXS"), b.can_short("UVIX")) == (True, False, False)
    assert len(c.calls) == 1                                  # no per-symbol GET for listed names
    assert b.borrow_known("SOXS") is False and b.borrow_known("ZZZZ") is None
    assert b.can_short("ZZZZ") is True and c.calls[-1] == ("get_asset", "ZZZZ")   # unlisted: per-symbol path as before


# ---------------------------------------------------------------- runner: refresh + once-per-day journaling
class _Brk:
    def __init__(self, etb=frozenset(), fail=False):
        self.etb, self.fail, self.loads, self.cache = set(etb), fail, 0, {}

    def load_borrow(self):
        self.loads += 1
        if self.fail:
            raise RuntimeError("down")
        self.cache = {s: (s in self.etb) for s in ("AAA", "BBB")}
        return len(self.cache)

    def borrow_known(self, s):
        return self.cache.get(s)

    def can_short(self, s):
        return self.cache.get(s, True)


def _bare(cfg_shorts):
    r = object.__new__(R.PaperRunner)
    r.cfg = {"shorts": cfg_shorts}
    r.health = {}
    return r


def test_refresh_off_by_flag_and_periodic_when_on():
    r = _bare({"borrow_prefetch": False})
    r.broker = _Brk()
    r._refresh_borrow(NOW)
    assert r.broker.loads == 0
    r = _bare({"borrow_prefetch": True, "borrow_refresh_min": 60})
    r.broker = _Brk(etb={"AAA"})
    r._refresh_borrow(NOW)
    r._refresh_borrow(NOW + pd.Timedelta(minutes=30))
    assert r.broker.loads == 1 and r.health["borrow_list"]["symbols"] == 2
    r._refresh_borrow(NOW + pd.Timedelta(minutes=61))
    assert r.broker.loads == 2


def test_refresh_failure_never_raises_and_gives_up_after_3():
    r = _bare({"borrow_prefetch": True, "borrow_refresh_min": 0})
    r.broker = _Brk(fail=True)
    for k in range(5):
        r._refresh_borrow(NOW + pd.Timedelta(minutes=k))
    assert r.broker.loads == 3 and "borrow_list" not in r.health


def test_borrow_blocked_only_short_only_setups_after_first_journal():
    r = _bare({"borrow_prefetch": True})
    r.broker = _Brk(etb={"AAA"})
    r.broker.load_borrow()
    short, long_, both = NS(name="S", side=-1), NS(name="L", side=1), NS(name="B")
    day = NOW.date()
    assert not r._borrow_blocked(short, "BBB", day)          # first time: the signal is drawn and journaled once
    r._etb_logged = {("BBB", "S", str(day))}
    assert r._borrow_blocked(short, "BBB", day)              # then no more signals there today
    assert not r._borrow_blocked(short, "AAA", day)          # ETB name: unaffected
    assert not r._borrow_blocked(long_, "BBB", day) and not r._borrow_blocked(both, "BBB", day)
    assert not r._borrow_blocked(NS(name="S", side="short"), "BBB", NOW.date() + pd.Timedelta(days=1))
    r.cfg["shorts"]["borrow_prefetch"] = False
    assert not r._borrow_blocked(short, "BBB", day)          # flag off: today's behaviour


def test_etb_skip_journaled_once_per_setup_symbol_day(tmp_path, monkeypatch):
    r, c, ctx = _xc_runner(tmp_path, monkeypatch, 9.99, 10.01)
    r.cfg.setdefault("shorts", {})["borrow_prefetch"] = True
    r.broker.can_short = lambda s: False
    for _ in range(3):
        r._enter(Signal("XYZ", "S", -1, 10, stop=11.0, target=8.0), 10.0, ("XYZ", "S"), ctx, NOW)
    s = r.journal.signals(r.run_id)
    assert list(s.reason) == ["not shortable/ETB"] and len(c.orders) == 0
    r.cfg["shorts"]["borrow_prefetch"] = False                # flag off: one line per signal, as today
    r._enter(Signal("XYZ", "S", -1, 10, stop=11.0, target=8.0), 10.0, ("XYZ", "S"), ctx, NOW)
    assert len(r.journal.signals(r.run_id)) == 2


# ---------------------------------------------------------------- U9-TGT quote pre-check
def _go(r, ctx, side, stop, target, ref=10.0):
    r._enter(Signal("XYZ", "A", side, 10, stop=stop, target=target), ref, ("XYZ", "A"), ctx, NOW)
    return r.journal.signals(r.run_id).iloc[-1]


def test_target_passed_at_quote_skipped_without_order(tmp_path, monkeypatch):
    r, c, ctx = _xc_runner(tmp_path, monkeypatch, 10.04, 10.05)
    r.live["skip_passed_at_quote"] = True
    s = _go(r, ctx, 1, stop=9.5, target=10.05)                # long: ask 10.05 already at the target
    assert s.status == "skipped" and s.reason.startswith("target passed at quote") and len(c.orders) == 0
    s = _go(r, ctx, 1, stop=9.5, target=10.20)                # target still ahead: submitted
    assert s.status == "submitted" and len(c.orders) == 1


def test_short_side_and_stop_passed(tmp_path, monkeypatch):
    r, c, ctx = _xc_runner(tmp_path, monkeypatch, 9.95, 9.96)
    r.live["skip_passed_at_quote"] = True
    r.broker.can_short = lambda s: True
    s = _go(r, ctx, -1, stop=10.5, target=9.96)               # short fills at bid 9.95: below the target already
    assert s.status == "skipped" and s.reason.startswith("target passed at quote")
    s = _go(r, ctx, 1, stop=9.95, target=11.0)                # long: bid 9.95 at the stop
    assert s.status == "skipped" and s.reason.startswith("stop passed at quote")
    assert len(c.orders) == 0


def test_flag_off_keeps_todays_path(tmp_path, monkeypatch):
    r, c, ctx = _xc_runner(tmp_path, monkeypatch, 10.04, 10.05)
    r.live["skip_passed_at_quote"] = False
    s = _go(r, ctx, 1, stop=9.5, target=10.05)
    assert s.status == "submitted"                           # today: the order goes to the broker


def test_default_config_turns_both_on():
    cfg = load_config()
    assert cfg["shorts"]["borrow_prefetch"] is True and cfg["shorts"]["borrow_refresh_min"] == 60
    assert cfg["live"]["skip_passed_at_quote"] is True


def test_skip_meta_carries_recheck_fields(tmp_path, monkeypatch):
    """Owner U9-TGT yes 2026-11-18: each skip records which quote side decided it, for the 10-session re-check."""
    import json

    r, c, ctx = _xc_runner(tmp_path, monkeypatch, 10.04, 10.05)
    r.live["skip_passed_at_quote"] = True
    m = json.loads(_go(r, ctx, 1, stop=9.5, target=10.05)["info"])
    assert m["u9_skip"] == "target" and m["u9_fill_side"] == 10.05 and m["u9_ref"] == 10.0
    r, c, ctx = _xc_runner(tmp_path / "b", monkeypatch, 9.95, 9.96)
    r.live["skip_passed_at_quote"] = True
    m = json.loads(_go(r, ctx, 1, stop=9.95, target=11.0)["info"])
    assert m["u9_skip"] == "stop" and m["u9_exit_side"] == 9.95 and len(c.orders) == 0
