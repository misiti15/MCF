"""BRAKE-BURST (owner 2026-11-20, research/whatworks_1120/brake/REPORT.md): runaway-entry brake in every account - at
most live.burst_max_entries new entries per setup in any rolling live.burst_window_min minutes; further signals of that
setup are skipped "burst brake" until the window clears. Educational only - not financial advice."""
import pandas as pd
import pytest

from mcf.config import load_config
from mcf.strategies.base import Signal
from tests.test_live_ready_lr import CTX, NY, _runner


def at(s):
    return pd.Timestamp(s, tz=NY)


def _sig(sym, setup="S1"):
    return Signal(sym, setup, 1, 4, stop=49.0, target=52.0)


def _go(r, sym, now, setup="S1"):
    r._enter(_sig(sym, setup), 50.0, (sym, setup), CTX, now)


@pytest.mark.parametrize("acct", ["primary", "testing", "testing2", "gen", "graveyard", "livelab", "explore1",
                                  "testingd", "testinge", "testingf"])
def test_config_every_account_30_in_10_minutes(acct, monkeypatch):
    monkeypatch.setenv("MCF_ACCOUNT", acct)
    lv = load_config()["live"]
    assert lv["burst_max_entries"] == 30 and lv["burst_window_min"] == 10


def test_runner_reads_config(tmp_path, monkeypatch):
    r, _ = _runner(tmp_path, monkeypatch)
    assert r.burst_max == 30 and r.burst_window == pd.Timedelta(minutes=10)


def _small(tmp_path, monkeypatch, n=3, win=10):
    r, b = _runner(tmp_path, monkeypatch)
    r.burst_max, r.burst_window = n, pd.Timedelta(minutes=win)
    r.today = at("2026-11-23 10:00").date()
    return r, b


def _statuses(r):
    s = r.journal.signals(r.run_id, str(r.today))
    return list(zip(s["symbol"], s["status"], s["reason"]))


def test_brake_skips_after_n_entries_until_window_clears(tmp_path, monkeypatch):
    r, b = _small(tmp_path, monkeypatch)
    t0 = at("2026-11-23 10:55")
    for i, sym in enumerate(["AAA", "BBB", "CCC"]):
        _go(r, sym, t0 + pd.Timedelta(minutes=i))
    assert len(b.submitted) == 3
    _go(r, "DDD", t0 + pd.Timedelta(minutes=3))                       # 4th within 10 min: braked
    _go(r, "EEE", t0 + pd.Timedelta(minutes=9, seconds=59))
    assert len(b.submitted) == 3
    rows = _statuses(r)
    assert ("DDD", "skipped", "burst brake") in rows and ("EEE", "skipped", "burst brake") in rows
    _go(r, "FFF", t0 + pd.Timedelta(minutes=10, seconds=1))           # the first entry left the window
    assert len(b.submitted) == 4


def test_brake_is_per_setup(tmp_path, monkeypatch):
    r, b = _small(tmp_path, monkeypatch, n=2)
    t0 = at("2026-11-23 11:00")
    _go(r, "AAA", t0)
    _go(r, "BBB", t0)
    _go(r, "CCC", t0)                                                 # S1 braked
    _go(r, "DDD", t0, setup="S2")                                     # another setup: unaffected
    assert len(b.submitted) == 3 and ("CCC", "skipped", "burst brake") in _statuses(r)


def test_off_when_zero(tmp_path, monkeypatch):
    r, b = _small(tmp_path, monkeypatch, n=0)
    t0 = at("2026-11-23 11:00")
    for i in range(5):
        _go(r, f"S{i}X", t0)
    assert len(b.submitted) == 5 and not any(w == "burst brake" for _, _, w in _statuses(r))


def test_braked_signals_do_not_extend_the_window(tmp_path, monkeypatch):
    r, b = _small(tmp_path, monkeypatch, n=1)
    t0 = at("2026-11-23 11:00")
    _go(r, "AAA", t0)
    for m in range(1, 10):
        _go(r, f"B{m}", t0 + pd.Timedelta(minutes=m))                  # all braked, none counted as an entry
    _go(r, "CCC", t0 + pd.Timedelta(minutes=10, seconds=30))
    assert len(b.submitted) == 2


def test_restart_restores_window_from_journal(tmp_path, monkeypatch):
    r, b = _small(tmp_path, monkeypatch, n=2)
    t0 = at("2026-11-23 11:00")
    _go(r, "AAA", t0)
    _go(r, "BBB", t0 + pd.Timedelta(minutes=1))
    r2, b2 = _runner(tmp_path, monkeypatch, broker=b)                 # same journal: a second CI job
    r2.burst_max = 2
    r2.restore(t0.date())
    assert r2._burst_count("S1", t0 + pd.Timedelta(minutes=2)) == 2
    _go(r2, "CCC", t0 + pd.Timedelta(minutes=2))
    assert len(b.submitted) == 2 and ("CCC", "skipped", "burst brake") in _statuses(r2)
