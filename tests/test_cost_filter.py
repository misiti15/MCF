"""Owner 2026-10-29 CF: Testing-only cost filter (live.max_stop_cost_r). Educational only - not financial advice."""
import os

from mcf.config import load_config
from mcf.strategies.base import Signal
from tests.test_outage import NOW, _xc_runner


def _go(r, ctx, stop):
    r._enter(Signal("XYZ", "A", 1, 10, stop=stop, target=12.0), 10.0, ("XYZ", "A"), ctx, NOW)
    return r.journal.signals(r.run_id).iloc[-1]


def test_cost_filter_skips_tight_stops_and_keeps_wide_ones(tmp_path, monkeypatch):
    r, c, ctx = _xc_runner(tmp_path, monkeypatch, 9.999, 10.001)
    r.live["max_stop_cost_r"] = 0.15
    s = _go(r, ctx, 9.80)            # (2 x (0.01 + 0.001) + 0.02) / 0.20 = 0.21R > 0.15
    assert s.status == "skipped" and s.reason.startswith("cost filter: stop-exit cost 0.21R")
    s = _go(r, ctx, 9.50)            # 0.042 / 0.50 = 0.084R
    assert s.status == "submitted" and len(c.orders) == 1


def test_cost_filter_off_unless_configured(tmp_path, monkeypatch):
    r, c, ctx = _xc_runner(tmp_path, monkeypatch, 9.999, 10.001)
    r.live.pop("max_stop_cost_r", None)
    assert _go(r, ctx, 9.80).status == "submitted"


def test_cost_filter_testing_accounts_only(monkeypatch):
    for acct, want in (("primary", None), ("gen", None), ("graveyard", None), ("testing", 0.15), ("testing2", 0.15)):
        monkeypatch.setenv("MCF_ACCOUNT", acct)
        assert load_config()["live"].get("max_stop_cost_r") == want, acct
