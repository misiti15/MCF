"""Split-tape short gate (owner 2026-10-14, research/bdi/bdi1013/NOTES.md G7; Testing 1 only): skip NEW shorts while
QQQ fromOpen - IWM fromOpen >= spread_pct. Off in config/default.yaml (Primary, Testing 2). Educational only."""
import json
from types import SimpleNamespace

import pandas as pd
import pytest

from mcf.config import load_config
from mcf.execution import runner as R
from mcf.report import playing_time as pt
from mcf.strategies.base import Signal

NY = "America/New_York"
NOW = pd.Timestamp("2026-10-14 10:30:05", tz=NY)


class Broker:
    def __init__(self):
        self.submitted = []

    def equity(self):
        return 1e5

    def can_short(self, symbol):
        return True

    def positions(self):
        return {}

    def submit_bracket(self, sig, qty, coid):
        self.submitted.append(coid)
        return SimpleNamespace(id=f"o{len(self.submitted)}")


def _tape(ret_pct, end="10:29", start="09:30"):
    idx = pd.date_range(f"2026-10-14 {start}", f"2026-10-14 {end}", freq="1min", tz=NY)
    df = pd.DataFrame({"open": 100.0, "high": 101.0, "low": 99.0, "close": 100.0, "volume": 1e6}, index=idx)
    df.iloc[-1, df.columns.get_loc("close")] = 100.0 * (1 + ret_pct / 100)
    return df


def _runner(tmp_path, monkeypatch, enabled=True, spread=0.50):
    cfg = load_config()
    cfg["data"]["journal_path"] = str(tmp_path / "j.db")
    cfg["live"]["split_tape_short_gate"] = {"enabled": enabled, "spread_pct": spread}
    r = R.PaperRunner(cfg, [], {"XYZ": object()}, broker=Broker())
    monkeypatch.setattr(r, "_realism", lambda sig, ctx, px: (True, "ok", {}))
    monkeypatch.setattr(R, "is_extended", lambda ctx, cfg: False)
    return r


def _enter(r, side):
    sig = Signal("XYZ", "S", side, 5, stop=9.0 if side == 1 else 11.0)
    ctx = SimpleNamespace(symbol="XYZ", bars=pd.DataFrame({"volume": [1e6] * 6}))
    r._enter(sig, 10.0, ("XYZ", "S"), ctx, NOW)
    s = r.journal.signals(r.run_id)
    row = s.iloc[-1]
    return row["status"], row["reason"], json.loads(row["info"] or "{}")


def test_default_off_primary_and_testing2(monkeypatch):
    for acct in ("primary", "testing2"):
        monkeypatch.setenv("MCF_ACCOUNT", acct)
        assert load_config()["live"]["split_tape_short_gate"] == {"enabled": False, "spread_pct": 0.50}
    monkeypatch.setenv("MCF_ACCOUNT", "testing")
    assert load_config()["live"]["split_tape_short_gate"] == {"enabled": True, "spread_pct": 0.50}


def test_watchlist_adds_qqq_iwm_only_when_on(tmp_path, monkeypatch):
    assert {"QQQ", "IWM"} <= set(_runner(tmp_path, monkeypatch).watchlist)
    off = _runner(tmp_path, monkeypatch, enabled=False)
    assert off.watchlist == ["XYZ"]


def test_gate_blocks_short_and_logs_info(tmp_path, monkeypatch):
    r = _runner(tmp_path, monkeypatch)
    r.bars = {"QQQ": _tape(0.80), "IWM": _tape(0.10)}
    st, why, info = _enter(r, -1)
    assert (st, why) == ("skipped", "split-tape short gate")
    assert info["qqq_ret"] == pytest.approx(0.80) and info["iwm_ret"] == pytest.approx(0.10)
    assert info["spread"] == pytest.approx(0.70)
    assert r.broker.submitted == []
    assert pt.classify(st, why) == "split_gate"


def test_longs_unaffected(tmp_path, monkeypatch):
    r = _runner(tmp_path, monkeypatch)
    r.bars = {"QQQ": _tape(1.50), "IWM": _tape(-1.0)}
    st, why, _ = _enter(r, 1)
    assert st == "submitted" and len(r.broker.submitted) == 1


def test_gate_off_passes_short(tmp_path, monkeypatch):
    r = _runner(tmp_path, monkeypatch, enabled=False)
    r.bars = {"QQQ": _tape(1.50), "IWM": _tape(-1.0)}
    assert _enter(r, -1)[0] == "submitted"


@pytest.mark.parametrize("qqq,iwm,blocked", [(0.50, 0.0, True), (0.49, 0.0, False), (0.30, -0.20, True),
                                             (0.0, -0.49, False), (-0.2, 0.5, False)])
def test_threshold_edge(tmp_path, monkeypatch, qqq, iwm, blocked):
    r = _runner(tmp_path, monkeypatch)
    r.bars = {"QQQ": _tape(qqq), "IWM": _tape(iwm)}
    st, why, _ = _enter(r, -1)
    assert (why == "split-tape short gate") is blocked
    assert (st == "submitted") is (not blocked)


def test_forming_bar_ignored(tmp_path, monkeypatch):
    """Only completed bars count: the 10:30 bar is still forming at 10:30:05."""
    r = _runner(tmp_path, monkeypatch)
    q = pd.concat([_tape(0.0), _tape(2.0, end="10:30", start="10:30")])
    r.bars = {"QQQ": q, "IWM": _tape(0.0)}
    assert _enter(r, -1)[0] == "submitted"


@pytest.mark.parametrize("bars", [{}, {"QQQ": _tape(1.0)}, {"QQQ": _tape(1.0), "IWM": _tape(0.0, end="10:20")}])
def test_missing_or_stale_data_passes_with_warning(tmp_path, monkeypatch, bars):
    r = _runner(tmp_path, monkeypatch)
    r.bars = dict(bars)
    assert _enter(r, -1)[0] == "submitted"
    assert "warning" in r.health["split_tape_gate"]
