"""Testing-account flags (owner 2026-10-13, research/bdi/longs1013 Q3): retry_after_release and longs_first_on_ties.
Both off in config/default.yaml (Primary byte-identical), on in the two Testing accounts. Educational only."""
import json
import os
from types import SimpleNamespace

import pandas as pd

from mcf.config import load_config
from mcf.execution import runner as R
from mcf.strategies.base import Signal

NY = "America/New_York"


class Broker:
    def __init__(self):
        self.submitted, self.held = [], {}

    def equity(self):
        return 1e5

    def can_short(self, symbol):
        return True

    def positions(self):
        return dict(self.held)

    def submit_bracket(self, sig, qty, coid):
        self.submitted.append(coid)
        self.held[sig.symbol] = SimpleNamespace(avg_entry_price=10.0)   # fills at once
        return SimpleNamespace(id=f"o{len(self.submitted)}")


class Strat:
    """Fires on the bars listed in `fire` (bar index -> side), market entry on that bar."""
    def __init__(self, name, fire):
        self.name, self.fire, self.params = name, fire, {}

    def eligible(self, ctx):
        return True

    def signals(self, ctx):
        last = len(ctx.bars) - 1
        return [Signal(ctx.symbol, self.name, side, i, stop=9.0 if side == 1 else 11.0)
                for i, side in self.fire.items() if i <= last]


def _bars(n):
    idx = pd.date_range("2026-10-13 10:00", periods=n, freq="1min", tz=NY)
    return pd.DataFrame({"open": 10.0, "high": 10.1, "low": 9.9, "close": 10.0, "volume": 1e6}, index=idx)


def _runner(tmp_path, monkeypatch, strategies, **flags):
    cfg = load_config()
    cfg["live"]["max_lots_per_symbol"] = 1   # retry semantics tested with one lot per symbol
    cfg["live"]["same_setup_reentry"] = False   # re-entry (2026-10-14) supersedes retry_after_release
    cfg["data"]["journal_path"] = str(tmp_path / "j.db")
    cfg["live"].update(flags)
    b = Broker()
    r = R.PaperRunner(cfg, strategies, {}, broker=b)
    monkeypatch.setattr(r, "_realism", lambda sig, ctx, px: (True, "ok", {}))
    monkeypatch.setattr(r, "manage", lambda now, bars: None)
    state = {"n": 1}
    monkeypatch.setattr(r, "fetch", lambda now: {"XYZ": _bars(state["n"])})
    monkeypatch.setattr(r, "_contexts", lambda bars, today: [SimpleNamespace(symbol="XYZ", bars=bars["XYZ"], avg_dollar_volume=5e8)])
    return r, b, state


def _poll(r, state, n):
    state["n"] = n
    now = pd.Timestamp("2026-10-13 10:00", tz=NY) + pd.Timedelta(minutes=n, seconds=5)
    r.step(now)
    r._sync_open()


def _rows(r):
    s = r.journal.signals(r.run_id)
    return [(x.strategy, x.status, x.reason, json.loads(x.info or "{}").get("retry_after_release")) for x in s.itertuples()]


def test_default_config_has_flags_off_and_testing_on(monkeypatch):
    monkeypatch.delenv("MCF_ACCOUNT", raising=False)
    live = load_config()["live"]
    assert live["retry_after_release"] is False and live["longs_first_on_ties"] is False
    for acct in ("testing", "testing2"):
        monkeypatch.setenv("MCF_ACCOUNT", acct)
        live = load_config()["live"]
        assert live["retry_after_release"] is True and live["longs_first_on_ties"] is True, acct


def _scenario(tmp_path, monkeypatch, **flags):
    # HOLD (short) takes XYZ on bar 0; LONG fires on bar 0 (blocked) and again on bar 3, 4 (fresh signals)
    hold, long_ = Strat("HOLD", {0: -1}), Strat("LONG", {0: 1, 3: 1, 4: 1})
    r, b, state = _runner(tmp_path, monkeypatch, [hold, long_], **flags)
    _poll(r, state, 1)                  # bar 0 complete: HOLD enters, LONG blocked
    _poll(r, state, 2)                  # still held
    b.held.pop("XYZ")                   # HOLD's stop/target fills
    r.pending.clear()
    _poll(r, state, 3)                  # bars 0..2: no fresh LONG signal on the latest bar
    _poll(r, state, 4)                  # bar 3 is the latest: fresh LONG signal
    b.held.pop("XYZ", None)
    r.pending.clear()
    _poll(r, state, 5)                  # bar 4: once per setup/symbol/day -> nothing
    return r, b


def test_retry_after_release_off_keeps_block_for_the_day(tmp_path, monkeypatch):
    r, b = _scenario(tmp_path, monkeypatch, retry_after_release=False)
    assert len(b.submitted) == 1
    assert _rows(r) == [("HOLD", "submitted", "ok", None), ("LONG", "skipped", "already in symbol", None)]


def test_retry_after_release_on_takes_next_fresh_signal_once(tmp_path, monkeypatch):
    r, b = _scenario(tmp_path, monkeypatch, retry_after_release=True)
    assert len(b.submitted) == 2 and "LONG-XYZ" in b.submitted[1]
    assert _rows(r) == [("HOLD", "submitted", "ok", None), ("LONG", "skipped", "already in symbol", None),
                        ("LONG", "submitted", "ok", True)]
    s = r.journal.signals(r.run_id)
    assert int(s.bar_index.iloc[-1]) == 3          # entry from the fresh signal on the latest bar, not the blocked one
    # restart: state rebuilt from the journal, the retry is spent
    r2 = R.PaperRunner(r.cfg, r.strategies, {}, broker=b, dry_run=True)
    r2.restore(pd.Timestamp("2026-10-13").date())
    assert r2.blocked[("XYZ", "LONG")]["done"] is True


def test_retry_waits_while_symbol_held(tmp_path, monkeypatch):
    hold, long_ = Strat("HOLD", {0: -1}), Strat("LONG", {0: 1, 2: 1, 3: 1})
    r, b, state = _runner(tmp_path, monkeypatch, [hold, long_], retry_after_release=True)
    for n in (1, 2, 3, 4):              # never released
        _poll(r, state, n)
    assert len(b.submitted) == 1 and len(_rows(r)) == 2
    assert r.blocked[("XYZ", "LONG")]["done"] is False


def test_longs_first_on_ties(tmp_path, monkeypatch):
    short, long_ = Strat("SHORT", {0: -1}), Strat("LONG", {0: 1})
    for flag, winner in ((False, "SHORT"), (True, "LONG")):
        d = tmp_path / str(flag)
        d.mkdir()
        r, b, state = _runner(d, monkeypatch, [short, long_], longs_first_on_ties=flag)
        _poll(r, state, 1)
        assert len(b.submitted) == 1 and f"{winner}-XYZ" in b.submitted[0], flag
        rows = _rows(r)
        assert [x[:3] for x in rows] == [(winner, "submitted", "ok"),
                                         ({"SHORT", "LONG"}.difference({winner}).pop(), "skipped", "already in symbol")]


def test_longs_first_keeps_setup_order_within_side(tmp_path, monkeypatch):
    a, b_, c = Strat("S1", {0: -1}), Strat("L1", {0: 1}), Strat("L2", {0: 1})
    r, b, state = _runner(tmp_path, monkeypatch, [a, b_, c], longs_first_on_ties=True)
    _poll(r, state, 1)
    assert [x[0] for x in _rows(r)] == ["L1", "L2", "S1"] and "L1-XYZ" in b.submitted[0]
