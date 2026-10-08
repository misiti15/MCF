"""Regression 2026-10-08: several setups firing on the same symbol in the same poll each opened a bracket (EDV x4),
because a just-submitted market entry is not yet a broker position and _sync_open dropped it from open_symbols."""
from types import SimpleNamespace

import pandas as pd

from mcf.config import load_config
from mcf.execution import runner as R
from mcf.strategies.base import Signal


class Broker:
    def __init__(self):
        self.submitted, self.held = [], {}

    def equity(self):
        return 1e5

    def can_short(self, symbol):
        return True

    def positions(self):          # the market entry has not filled yet
        return dict(self.held)

    def submit_bracket(self, sig, qty, coid):
        self.submitted.append(coid)
        return SimpleNamespace(id=f"o{len(self.submitted)}")


def _runner(tmp_path, monkeypatch):
    cfg = load_config()
    cfg["data"]["journal_path"] = str(tmp_path / "j.db")
    b = Broker()
    r = R.PaperRunner(cfg, [], {}, broker=b)
    r.dry_run = False
    monkeypatch.setattr(r, "_realism", lambda sig, ctx, px: (True, "ok", {}))
    return r, b


def test_same_symbol_same_poll_enters_once(tmp_path, monkeypatch):
    r, b = _runner(tmp_path, monkeypatch)
    now = pd.Timestamp("2026-10-08 09:50:30", tz="America/New_York")
    ctx = SimpleNamespace(bars=pd.DataFrame({"volume": [1e6] * 5}), avg_dollar_volume=5e8)
    for name in ("MF5", "MF4", "MF3", "MF1"):
        r._enter(Signal("EDV", name, -1, 10, stop=55.0, target=54.0), 54.45, (name, "EDV"), ctx, now)
    assert len(b.submitted) == 1


def test_pending_entry_expires_if_it_never_fills(tmp_path, monkeypatch):
    r, b = _runner(tmp_path, monkeypatch)
    now = pd.Timestamp("2026-10-08 09:50:30", tz="America/New_York")
    ctx = SimpleNamespace(bars=pd.DataFrame({"volume": [1e6] * 5}), avg_dollar_volume=5e8)
    r._enter(Signal("EDV", "MF5", -1, 10, stop=55.0, target=54.0), 54.45, ("MF5", "EDV"), ctx, now)
    r.pending["EDV"] -= r.PENDING_GRACE_S + 1
    r._sync_open()
    assert "EDV" not in r.risk.state.open_symbols
