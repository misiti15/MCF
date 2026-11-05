"""HK-HALT-RESTART (2026-11-05): the day's sticky latches and counters survive a job restart / hand-over.

Gen 11-05: the account daily-loss halt fired at 14:10 ET; open lots then closed green, so by the 14:40 hand-over the
journal's net R (-119.7) was back above the -120R limit and the 14:49 successor, which only re-checked the current net,
took 32 more entries. These tests run one runner until a latch fires, then start a NEW runner on the same journal (same
day) and check it is still latched. Educational only - not financial advice."""
from types import SimpleNamespace

import pandas as pd

from mcf.config import load_config
from mcf.execution import runner as R
from mcf.strategies.base import Signal
from tests.test_no_stacking import Broker

NY = "America/New_York"
CTX = SimpleNamespace(bars=pd.DataFrame({"volume": [1e6] * 5}), avg_dollar_volume=5e8)


def _cfg(tmp_path, setup_limit=None):
    cfg = load_config()
    cfg["live"]["max_lots_per_symbol"] = 1
    cfg["data"]["journal_path"] = str(tmp_path / "j.db")
    cfg["account"]["max_daily_loss_r"] = 10
    cfg["account"]["max_setup_daily_loss_r"] = setup_limit
    return cfg


def _runner(cfg, monkeypatch):
    b = Broker()
    r = R.PaperRunner(cfg, [], {}, broker=b)
    monkeypatch.setattr(r, "_realism", lambda sig, ctx, px: (True, "ok", {}))
    monkeypatch.setattr(r, "_restore_from_broker", lambda today: None)   # fake broker: no order history
    return r, b


def _sig(sym, strat):
    return Signal(sym, strat, -1, 4, stop=55.0, target=54.0)


def _trades(day, rows):
    return pd.DataFrame([{"symbol": s, "strategy": st, "side": -1, "date": str(day), "signal_time": f"{day} 10:00",
                          "entry_time": f"{day} 10:00", "entry": 54.5, "stop": 55.0, "target": 54.0,
                          "exit_time": f"{day} {t}", "exit": 54.5, "exit_reason": "stop", "r_multiple": rr,
                          "success": int(rr > 0), "shares": 10, "pnl": rr * 5} for s, st, t, rr in rows])


def _last_signal(r, day):
    return r.journal.signals(r.run_id, str(day)).iloc[-1]


def test_account_halt_survives_restart_after_recovery(tmp_path, monkeypatch):
    now = pd.Timestamp("2026-11-05 14:10:00", tz=NY)
    day = now.date()
    cfg = _cfg(tmp_path)
    r1, b1 = _runner(cfg, monkeypatch)
    r1.restore(day)
    r1._enter(_sig("AAA", "S1"), 54.45, ("AAA", "S1"), CTX, now)
    assert len(b1.submitted) == 1
    # -10.5R reconciled: the halt fires on the next signal
    r1.journal.add_trades(r1.run_id, _trades(day, [("X", "S1", "14:00", -6.0), ("Y", "S2", "14:05", -4.5)]))
    r1.risk.state.realized_r = -10.5
    r1._enter(_sig("BBB", "S1"), 54.45, ("BBB", "S1"), CTX, now)
    assert r1.risk.state.halted and _last_signal(r1, day).reason == "daily loss limit"
    # an open lot then closes green: net -9.5R, above the -10R limit
    r1.journal.add_trades(r1.run_id, _trades(day, [("Z", "S3", "14:30", 1.0)]))

    r2, b2 = _runner(cfg, monkeypatch)             # successor job, same day
    r2.restore(day)
    assert r2.risk.state.realized_r == -9.5        # counters continue from the journal
    assert r2.risk.state.trades_today == 1
    assert r2.risk.state.halted
    r2._enter(_sig("CCC", "S2"), 54.45, ("CCC", "S2"), CTX, now + pd.Timedelta(minutes=40))
    assert b2.submitted == [] and _last_signal(r2, day).reason == "halted"


def test_no_halt_restored_when_it_never_fired(tmp_path, monkeypatch):
    now = pd.Timestamp("2026-11-05 11:00:00", tz=NY)
    day = now.date()
    cfg = _cfg(tmp_path)
    r1, _ = _runner(cfg, monkeypatch)
    r1.restore(day)
    r1.journal.add_trades(r1.run_id, _trades(day, [("X", "S1", "10:30", -9.0)]))
    r2, b2 = _runner(cfg, monkeypatch)
    r2.restore(day)
    assert not r2.risk.state.halted
    r2._enter(_sig("CCC", "S2"), 54.45, ("CCC", "S2"), CTX, now)
    assert len(b2.submitted) == 1


def test_halt_from_an_earlier_day_is_not_restored(tmp_path, monkeypatch):
    cfg = _cfg(tmp_path)
    r1, _ = _runner(cfg, monkeypatch)
    prev = pd.Timestamp("2026-11-04 14:00:00", tz=NY)
    r1.restore(prev.date())
    r1.risk.state.realized_r = -11
    r1._enter(_sig("BBB", "S1"), 54.45, ("BBB", "S1"), CTX, prev)
    assert r1.risk.state.halted
    r2, b2 = _runner(cfg, monkeypatch)
    now = pd.Timestamp("2026-11-05 10:00:00", tz=NY)
    r2.restore(now.date())
    assert not r2.risk.state.halted
    r2._enter(_sig("CCC", "S2"), 54.45, ("CCC", "S2"), CTX, now)
    assert len(b2.submitted) == 1


def test_setup_latch_survives_restart(tmp_path, monkeypatch):
    """Primary's -2R per-setup latch: X latched in job 1 stays blocked in job 2; Y keeps trading."""
    now = pd.Timestamp("2026-11-05 11:00:00", tz=NY)
    day = now.date()
    cfg = _cfg(tmp_path, setup_limit=2.0)
    r1, _ = _runner(cfg, monkeypatch)
    r1.restore(day)
    r1.risk.state.realized_r_by_strategy = {"X": -2.0}
    r1._enter(_sig("AAA", "X"), 54.45, ("AAA", "X"), CTX, now)
    assert "X" in r1.risk.state.setup_stopped and _last_signal(r1, day).reason == "setup daily loss limit"
    # no trade rows for X in the journal here: the journaled latch alone keeps X stopped
    r2, b2 = _runner(cfg, monkeypatch)
    r2.restore(day)
    assert r2.risk.state.setup_stopped == {"X"}
    r2._enter(_sig("BBB", "X"), 54.45, ("BBB", "X"), CTX, now)
    assert b2.submitted == [] and _last_signal(r2, day).reason == "setup daily loss limit"
    r2._enter(_sig("CCC", "Y"), 54.45, ("CCC", "Y"), CTX, now)
    assert len(b2.submitted) == 1


def test_setup_latch_restored_from_trades_after_recovery(tmp_path, monkeypatch):
    now = pd.Timestamp("2026-11-05 12:00:00", tz=NY)
    day = now.date()
    cfg = _cfg(tmp_path, setup_limit=2.0)
    r1, _ = _runner(cfg, monkeypatch)
    r1.restore(day)
    r1.journal.add_trades(r1.run_id, _trades(day, [("A", "X", "10:00", -1.0), ("B", "X", "10:30", -1.2),
                                                    ("C", "X", "11:00", 2.0), ("D", "Y", "11:05", -1.0)]))
    r2, b2 = _runner(cfg, monkeypatch)
    r2.restore(day)
    assert r2.risk.state.setup_stopped == {"X"}
    assert round(r2.risk.state.realized_r_by_strategy["X"], 6) == -0.2
    r2._enter(_sig("EEE", "X"), 54.45, ("EEE", "X"), CTX, now)
    r2._enter(_sig("FFF", "Y"), 54.45, ("FFF", "Y"), CTX, now)
    assert len(b2.submitted) == 1


def test_counters_and_held_symbols_continue(tmp_path, monkeypatch):
    """trades_today and the held symbol (already in symbol / per-setup position caps) carry over to the successor."""
    now = pd.Timestamp("2026-11-05 10:00:00", tz=NY)
    day = now.date()
    cfg = _cfg(tmp_path)
    r1, b1 = _runner(cfg, monkeypatch)
    r1.restore(day)
    for sym in ("AAA", "BBB", "CCC"):
        r1._enter(_sig(sym, "S1"), 54.45, (sym, "S1"), CTX, now)
    assert r1.risk.state.trades_today == 3
    r2, b2 = _runner(cfg, monkeypatch)
    b2.held = {"AAA": 1, "BBB": 1, "CCC": 1}
    r2.restore(day)
    assert r2.risk.state.trades_today == 3
    assert r2.risk.state.open_symbols == {"AAA", "BBB", "CCC"}
    assert r2.risk.state.open_by_strategy == {"S1": 3}
    r2._enter(_sig("AAA", "S2"), 54.45, ("AAA", "S2"), CTX, now + pd.Timedelta(minutes=5))
    assert b2.submitted == [] and _last_signal(r2, day).reason == "already in symbol"


def test_status_shows_risk_state(tmp_path, monkeypatch):
    cfg = _cfg(tmp_path)
    r, _ = _runner(cfg, monkeypatch)
    r.risk.state.halted = True
    r.risk.state.setup_stopped = {"X"}
    r.write_status(pd.Timestamp("2026-11-05 14:00", tz=NY), "trading")
    assert r.health["risk_state"]["halted"] is True and r.health["risk_state"]["setup_stopped"] == ["X"]
