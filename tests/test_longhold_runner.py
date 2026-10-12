"""Long-hold (S6) runner on a fake broker and synthetic bars: no network, no orders. Educational only."""
import json
from datetime import date, datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from mcf.longhold import core, signals
from mcf.longhold.broker import KeySeparationError, check_key_separation
from mcf.longhold.runner import ET, Runner, load_config, size_orders

DATA = Path(__file__).parent / "data"


# ---------------------------------------------------------------------------------------------- fakes
def synth_bars(n_sym=60, end="2026-10-12", n_days=320, seed=7):
    days = pd.bdate_range(end=end, periods=n_days)
    rng = np.random.default_rng(seed)
    rows = []
    for i in range(n_sym):
        s = f"S{i:02d}"
        drift = rng.normal(0.0005, 0.001)
        px = 50 * np.exp(np.cumsum(rng.normal(drift, 0.02, n_days)))
        for d, p in zip(days, px):
            rows.append((s, d, p, p * 1.01, p * 0.99, p, 2e6))
    spy = 400 * np.exp(np.cumsum(rng.normal(0.0003, 0.01, n_days)))
    rows += [("SPY", d, p, p, p, p, 5e7) for d, p in zip(days, spy)]
    return pd.DataFrame(rows, columns=["symbol", "date", "open", "high", "low", "close", "volume"])


class FakeData:
    def __init__(self, bars):
        self.all = bars
        self.calls = []

    def bars(self, symbols, start, end, adjustment="all"):
        self.calls.append((len(symbols), str(start), str(end), adjustment))
        b = self.all
        return b[b.symbol.isin(symbols) & (b.date >= pd.Timestamp(start)) & (b.date <= pd.Timestamp(end))].copy()


class FakeBroker:
    def __init__(self, equity=100000.0, positions=None, days=None):
        self.eq = equity
        self.pos = positions or {}
        self.days = days
        self.orders_ = []
        self.submits = 0

    def account(self):
        return {"equity": self.eq, "cash": self.eq - sum(p["market_value"] for p in self.pos.values()),
                "last_equity": self.eq, "trading_blocked": False}

    def positions(self):
        return dict(self.pos)

    def calendar(self, start, end):
        return [d for d in self.days if start <= d <= end]

    def tradable(self, symbol):
        return True

    def orders(self, prefix, after):
        assert prefix.startswith("mcl-")
        return [o for o in self.orders_ if o["client_order_id"].startswith(prefix)]

    def submit(self, symbol, qty, side, tif, client_order_id):
        self.submits += 1
        if any(o["client_order_id"] == client_order_id for o in self.orders_):
            raise RuntimeError('{"code":40010001,"message":"client_order_id must be unique"}')
        self.orders_.append({"client_order_id": client_order_id, "symbol": symbol, "qty": qty, "side": side,
                             "time_in_force": tif, "status": "accepted"})
        return {"client_order_id": client_order_id, "status": "accepted"}


def calendar_days(end="2026-10-30"):
    return [d.date() for d in pd.bdate_range("2025-01-01", end)]


def make(tmp_path, bars=None, broker=None, live=True, now="2026-10-12T14:00", **kw):
    bars = synth_bars() if bars is None else bars
    days = calendar_days()
    broker = broker or FakeBroker(days=days)
    broker.days = days
    syms = sorted(set(bars.symbol) - {"SPY"})
    cfg = load_config()
    r = Runner(tmp_path, FakeData(bars), broker=broker if live else None, calendar=broker, live=live,
               now=datetime.fromisoformat(now).replace(tzinfo=ET), cfg=cfg, etf=set(), universe=syms, **kw)
    return r, broker


# ---------------------------------------------------------------------------------------------- signal parity
def test_signal_parity_with_study_on_frozen_slice():
    """Targets from mcf.longhold.signals equal those of research/longhold/study.py's own code (executed from its
    source by research/longhold/make_parity_fixture.py) on a frozen slice, for 3 weekly signal days."""
    raw = pd.read_csv(DATA / "longhold_parity.csv.gz")
    raw["date"] = pd.to_datetime(raw["date"])
    exp = json.loads((DATA / "longhold_parity_expected.json").read_text())
    assert exp["strategy"] == signals.STRATEGY
    days = sorted(exp["signal_days"])
    assert len(days) == 3
    etf = signals.etf_set()                       # the fixture's ETFs (SPY/QQQ/XLK) are tagged via assets_meta
    for d in days:
        got = signals.compute(raw, date.fromisoformat(d), etf)
        assert got["reason"] is None
        assert got["targets"] == exp["signal_days"][d], d
        assert len(got["targets"]) == 20 and abs(sum(got["targets"].values()) - 1) < 1e-9


# ---------------------------------------------------------------------------------------------- init (MOC)
def test_init_submits_each_moc_order_once(tmp_path):
    r, b = make(tmp_path)
    plan = r.init("all")
    assert plan["signal_day"] == "2026-10-09" and plan["exec_day"] == "2026-10-12"
    assert plan["status"] == "submitted" and plan["time_in_force"] == "cls"
    n = len(plan["orders"])
    assert 15 <= n <= 20 and all(o["side"] == "buy" and isinstance(o["qty"], int) and o["qty"] >= 1
                                 for o in plan["orders"])
    assert all(o["client_order_id"].startswith("mcl-S6_mom12_1rev_N20_W-20261009-") for o in plan["orders"])
    assert sum(o["notional"] for o in plan["orders"]) <= 100000 * 0.99 + 1e-6      # cash buffer, no margin
    assert len(b.orders_) == n and all(o["time_in_force"] == "cls" for o in b.orders_)
    assert (tmp_path / "longhold" / "plans" / "2026-10-09.json").exists()
    assert (tmp_path / "longhold" / "LIVE").exists()
    # re-run (doubled trigger): the plan is reused, nothing new is submitted
    r2, _ = make(tmp_path, broker=b, now="2026-10-12T14:30")
    r2.init("all")
    assert len(b.orders_) == n and b.submits == n
    # broker forgot to list one order (eventual consistency): resubmission hits the duplicate-id reject
    b.orders = lambda prefix, after: []
    r3, _ = make(tmp_path, broker=b, now="2026-10-12T15:00")
    p3 = r3.init("submit")
    assert len(b.orders_) == n and p3["status"] == "submitted"
    assert all(v["status"] == "already placed" for v in p3["submissions"].values())


def test_init_plan_stage_then_submit_stage(tmp_path):
    r, b = make(tmp_path)
    p = r.init("plan")
    assert p["status"] == "planned" and not b.orders_
    r2, _ = make(tmp_path, broker=b)
    assert r2.init("submit")["status"] == "submitted" and len(b.orders_) == len(p["orders"])


def test_init_refuses_non_empty_account_and_late_submit(tmp_path):
    b = FakeBroker(positions={"S01": {"qty": 10, "market_value": 500.0, "current_price": 50.0}})
    r, _ = make(tmp_path, broker=b)
    with pytest.raises(RuntimeError, match="empty account"):
        r.init("all")
    r2, b2 = make(tmp_path / "late", now="2026-10-12T15:47")
    p = r2.init("all")
    assert p["status"] == "planned" and not b2.orders_


def test_data_sanity_stale_bars_place_no_orders(tmp_path):
    bars = synth_bars()
    bars = bars[bars.date < "2026-10-09"]                       # the signal day's bars are missing
    r, b = make(tmp_path, bars=bars)
    p = r.init("all")
    assert p["status"] == "skipped_data" and not p["orders"] and not b.orders_
    st = json.loads((tmp_path / "longhold" / "status.json").read_text())
    assert any(a["kind"] == "data_sanity" for a in st["alerts"])


def test_data_sanity_missing_spy_and_missing_names(tmp_path):
    bars = synth_bars()
    r, _ = make(tmp_path, bars=bars)
    assert r.sanity(bars[bars.symbol != "SPY"], date(2026, 10, 9)) == "SPY has no bar on the signal day"
    drop = bars[(bars.date == "2026-10-09") & bars.symbol.isin([f"S{i:02d}" for i in range(10)])].index
    assert "eligible names have no bar" in r.sanity(bars.drop(drop), date(2026, 10, 9))
    assert r.sanity(bars, date(2026, 10, 9)) is None


def test_halt_file_blocks_all_orders_and_keeps_holdings(tmp_path):
    (tmp_path / "longhold").mkdir(parents=True)
    (tmp_path / "longhold" / "HALT").write_text("owner")
    r, b = make(tmp_path)
    p = r.init("all")
    assert p["status"] == "halted" and not b.orders_ and b.submits == 0


def test_halt_file_added_after_plan_blocks_submit(tmp_path):
    r, b = make(tmp_path)
    r.init("plan")
    (tmp_path / "longhold" / "HALT").write_text("owner")
    r2, _ = make(tmp_path, broker=b)
    assert r2.init("submit")["status"] == "halted" and not b.orders_


def test_drawdown_kill_switch_blocks_orders(tmp_path):
    d = tmp_path / "longhold"
    d.mkdir(parents=True)
    pd.DataFrame({"date": ["2026-10-07", "2026-10-08"], "equity": [100000, 70000]}).to_csv(d / "marks.csv", index=False)
    r, b = make(tmp_path)
    assert r.init("all")["status"] == "halted" and not b.orders_


def test_dry_run_places_no_orders(tmp_path):
    days = calendar_days()
    cal = FakeBroker(days=days)
    r, _ = make(tmp_path, broker=cal, live=False)
    p = r.init("all")
    assert p["mode"] == "dry-run" and p["status"] == "planned" and len(p["orders"]) >= 15
    assert cal.submits == 0 and not cal.orders_
    with pytest.raises(RuntimeError):
        Runner(tmp_path, FakeData(synth_bars()), broker=None, calendar=cal, live=True)


def test_key_separation_refusal():
    base = {"ALPACA_API_KEY": "PRIMARY", "ALPACA_TESTING_API_KEY": "TEST1", "ALPACA_TRADE_SECRET_KEY": "x"}
    with pytest.raises(KeySeparationError):
        check_key_separation({**base})                                    # no trade key
    with pytest.raises(KeySeparationError, match="ALPACA_API_KEY"):
        check_key_separation({**base, "ALPACA_TRADE_API_KEY": "PRIMARY"})
    with pytest.raises(KeySeparationError, match="TESTING"):
        check_key_separation({**base, "ALPACA_TRADE_API_KEY": "TEST1"})
    with pytest.raises(KeySeparationError, match="TESTING2"):
        check_key_separation({**base, "ALPACA_TESTING2_API_KEY": "T2", "ALPACA_TRADE_API_KEY": "T2"})
    assert check_key_separation({**base, "ALPACA_TRADE_API_KEY": "LONGHOLD"}) == "ok"


def test_cli_live_switch(tmp_path):
    from argparse import Namespace

    from mcf.longhold.__main__ import is_live

    a = Namespace(dry_run=False)
    assert not is_live(a, {"ALPACA_TRADE_API_KEY": "K"})                          # LONGHOLD_LIVE defaults to false
    assert not is_live(a, {"LONGHOLD_LIVE": "true"})                              # no keys -> dry
    assert is_live(a, {"LONGHOLD_LIVE": "true", "ALPACA_TRADE_API_KEY": "K"})
    assert not is_live(Namespace(dry_run=True), {"LONGHOLD_LIVE": "true", "ALPACA_TRADE_API_KEY": "K"})
    (tmp_path / "longhold").mkdir()
    (tmp_path / "longhold" / "LIVE").write_text("x")
    assert is_live(a, {"ALPACA_TRADE_API_KEY": "K"}, state_dir=tmp_path)            # book already live
    assert not is_live(a, {}, state_dir=tmp_path)


def test_size_orders_whole_shares_and_funding():
    d = date(2026, 10, 9)
    orders = core.diff_orders({"A": 0.5, "B": 0.5}, {"C": 3000.0}, 10000.0, "x", d, band=0.0)
    out, notes = size_orders(orders, {"A": 33.0, "B": 7.0, "C": 30.0}, {"C": 100}, cash=7000.0, equity=10000.0,
                             buffer=0.01, targets={"A": 0.5, "B": 0.5})
    assert [o["side"] for o in out] == ["sell", "buy", "buy"]
    assert out[0]["qty"] == 100                                   # leaving name: whole position
    assert sum(o["notional"] for o in out if o["side"] == "buy") <= 7000 + 3000 - 100
    assert all(isinstance(o["qty"], int) for o in out)


def test_mark_writes_equity_and_drawdown(tmp_path):
    r, b = make(tmp_path, now="2026-10-12T18:30")
    row = r.mark()
    assert row["equity"] == 100000 and row["drawdown"] == 0 and row["spy_ret"] is not None
    st = json.loads((tmp_path / "longhold" / "status.json").read_text())
    assert st["label"] == "paper" and "not financial advice" in st["disclaimer"]


def test_dry_plan_is_rebuilt_for_live(tmp_path):
    cal = FakeBroker(days=calendar_days())
    r, _ = make(tmp_path, broker=cal, live=False)
    assert r.init("plan")["mode"] == "dry-run"
    b = FakeBroker(equity=50000.0)
    r2, _ = make(tmp_path, broker=b)
    p = r2.init("all")
    assert p["mode"] == "paper" and p["equity"] == 50000.0 and len(b.orders_) == len(p["orders"])
