"""Owner 2026-10-27: Primary positions ~$4,000 (77 slots); the testing accounts keep their own sizing."""
import os

from mcf.backtest.engine import slot_notional
from mcf.config import load_config


def _acct(name, monkeypatch):
    monkeypatch.setenv("MCF_ACCOUNT", name)
    return load_config()["account"]


def test_primary_slot_about_4000(monkeypatch):
    a = _acct("primary", monkeypatch)
    assert a["slots"] == a["max_concurrent_positions"] == 77 and a["max_positions_per_strategy"] == 30
    assert 3900 <= slot_notional({**a, "equity": 95718.71}) <= 4100
    assert a["slots"] * slot_notional({**a, "equity": 95718.71}) <= 321000   # inside paper intraday buying power


def test_testing_accounts_unchanged(monkeypatch):
    assert _acct("testing", monkeypatch)["slots"] == 400
    assert _acct("testing2", monkeypatch)["slots"] == 400
