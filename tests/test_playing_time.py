"""Playing-time report on a synthetic journal. Educational only - not financial advice."""
import json

import pandas as pd

from mcf.journal import Journal
from mcf.report import eod, playing_time as pt, scorecard


def _sig(j, run, day, ts, sym, strat, status, reason, info=""):
    j.record_signal(run, day, f"{day}T{ts}:00-04:00", sym, strat, -1, 10.0, 10.5, None, "market", None, 0,
                    status, reason, 1 if status == "submitted" else 0, None, info)


def _journal(tmp_path):
    j = Journal(tmp_path / "j.db")
    run = j.get_or_create_run("paper", "MCF Update (live paper)")
    d1, d2 = "2026-10-08", "2026-10-09"
    # day 1: WIDE takes AAA, NARROW then finds it held (older row: no held_by in info -> inferred)
    _sig(j, run, d1, "10:00", "AAA", "WIDE", "submitted", "ok")
    _sig(j, run, d1, "10:05", "AAA", "NARROW", "skipped", "already in symbol")
    _sig(j, run, d1, "10:10", "BBB", "WIDE", "skipped", "max concurrent positions")
    _sig(j, run, d1, "10:15", "CCC", "WIDE", "skipped", "not shortable/ETB")
    _sig(j, run, d1, "09:40", "DDD", "WIDE", "shadow", "before 09:50 (owner rule)")
    # day 2: runner logs held_by (2026-10-12 logging); NARROW loses twice more, takes one
    _sig(j, run, d2, "10:00", "EEE", "WIDE", "submitted", "ok")
    _sig(j, run, d2, "10:00", "EEE", "NARROW", "skipped", "already in symbol", json.dumps({"held_by": "WIDE"}))
    _sig(j, run, d2, "10:30", "FFF", "WIDE", "submitted", "ok")
    _sig(j, run, d2, "10:31", "FFF", "NARROW", "skipped", "already in symbol", json.dumps({"held_by": "WIDE"}))
    _sig(j, run, d2, "11:00", "GGG", "NARROW", "submitted", "ok")
    _sig(j, run, d2, "11:10", "HHH", "WIDE", "skipped", "spread 40bps > max")
    _sig(j, run, d2, "11:20", "III", "WIDE", "skipped", "max positions for this setup")
    _sig(j, run, d2, "11:30", "JJJ", "WIDE", "skipped", "daily loss limit")
    j.add_trades(run, pd.DataFrame([
        {"symbol": "AAA", "strategy": "WIDE", "side": -1, "date": d1, "entry_time": f"{d1}T14:00:00Z",
         "exit_time": f"{d1}T15:00:00Z", "entry": 10, "exit": 9.8, "stop": 10.5, "r_multiple": 0.4, "pnl": 2.0},
        {"symbol": "EEE", "strategy": "WIDE", "side": -1, "date": d2, "entry_time": f"{d2}T14:00:00Z",
         "exit_time": f"{d2}T15:00:00Z", "entry": 10, "exit": 10.2, "stop": 10.5, "r_multiple": -0.4, "pnl": -2.0},
        {"symbol": "GGG", "strategy": "NARROW", "side": -1, "date": d2, "entry_time": f"{d2}T14:30:00Z",
         "exit_time": f"{d2}T15:30:00Z", "entry": 10, "exit": 9.9, "stop": 10.5, "r_multiple": 0.2, "pnl": 1.0},
    ]))
    return j, run


def _state(tmp_path):
    st = tmp_path / "state"
    (st / "setups").mkdir(parents=True)
    snap = {"strategies": {"WIDE": {"enabled": True}, "NARROW": {"enabled": True}, "QUIET": {"enabled": True},
                           "OFF": {"enabled": False}},
            "live": {"setup_order": ["NARROW", "QUIET", "WIDE"]}}
    for d in ("2026-10-08", "2026-10-09"):
        (st / "setups" / f"{d}.json").write_text(json.dumps(snap))
    (st / "earnings").mkdir()
    (st / "earnings" / "2026-10-09.json").write_text(json.dumps({"symbols": {"X": [], "Y": []}}))
    return st


def test_classify_buckets():
    assert pt.classify("submitted", "ok") == "taken"
    assert pt.classify("dry_run", "dry run") == "taken"
    assert pt.classify("shadow", "before 09:50 (owner rule)") == "window"
    assert pt.classify("skipped", "already in symbol") == "held_by_other"
    assert pt.classify("skipped", "max concurrent positions") == "slots_full"
    assert pt.classify("skipped", "max positions for this setup") == "setup_cap"
    assert pt.classify("skipped", "max trades/day") == "trades_cap"
    assert pt.classify("skipped", "daily loss limit") == "daily_loss"
    assert pt.classify("skipped", "halted") == "daily_loss"
    assert pt.classify("skipped", "missed: triggered at 11:05") == "missed_trigger"
    assert pt.classify("skipped", "not shortable/ETB") == "borrow"
    assert pt.classify("skipped", "spread is 31% of stop distance") == "realism"
    assert pt.classify("skipped", "size < 1 share after liquidity cap") == "realism"
    assert pt.classify("skipped", "price already through stop") == "price"
    assert pt.classify("rejected", "insufficient buying power") == "rejected"
    assert pt.classify("skipped", "something new") == "other"


def test_report_counts_preemption_and_holders(tmp_path):
    j, run = _journal(tmp_path)
    st = _state(tmp_path)
    exp = {"WIDE": {"per_day": 3.0, "source": "test"}, "NARROW": {"per_day": 1.0, "source": "test"},
           "QUIET": {"per_day": 2.0, "source": "test"}}
    cfg = {"account_name": "testing", "account": {"max_concurrent_positions": 400},
           "strategies": {"WIDE": {"enabled": True}, "NARROW": {"enabled": True}, "QUIET": {"enabled": True}},
           "live": {"setup_order": ["NARROW", "QUIET", "WIDE"]}}
    import mcf.report.playing_time as mod
    orig = mod.expected_rates
    mod.expected_rates = lambda account="primary", root=None: exp
    try:
        rep = pt.from_journal(j, run, "2026-10-09", cfg, st)
    finally:
        mod.expected_rates = orig
    cum = {r["setup"]: r for r in rep["cumulative"]["setups"]}
    n = cum["NARROW"]
    assert n["signals"] == 4 and n["entries"] == 1 and n["trades"] == 1 and n["sessions"] == 2
    assert n["skipped"] == {"held_by_other": 3}
    assert n["lost_to"] == {"WIDE": 3}
    assert n["lost_to_higher_priority"] == 0 and n["lost_to_earlier_lower_priority"] == 3   # WIDE ranks below NARROW
    assert n["verdict"] == "crowded-out" and n["priority"] == 1
    w = cum["WIDE"]
    assert w["took_from_others"] == 3 and w["entries"] == 3 and w["signals"] == 9
    assert w["skipped"] == {"slots_full": 1, "borrow": 1, "window": 1, "realism": 1, "setup_cap": 1, "daily_loss": 1}
    q = cum["QUIET"]
    assert q["signals"] == 0 and q["sessions"] == 2 and q["verdict"] == "watch"   # 4 expected, but < 3 sessions
    assert "OFF" not in cum
    s = rep["cumulative"]["summary"]
    assert s["lost_to_other_setups"] == 3 and s["signals"] == 13 and s["entries"] == 4
    assert s["crowded_out"] == ["NARROW"]
    t = rep["today"]["summary"]
    assert t["setups_live"] == 3 and t["slots"] == 400 and t["earnings_excluded"] == 2 and t["lost_to_other_setups"] == 2
    assert t["peak_open_positions"] == 2   # EEE 14:00-15:00 overlaps GGG 14:30-15:30
    today = {r["setup"]: r for r in rep["today"]["setups"]}
    assert today["NARROW"]["signals"] == 3 and today["NARROW"]["lost_to"] == {"WIDE": 2}
    json.dumps(rep)   # serialisable for scorecard.json


def test_verdicts():
    assert pt._verdict(0, 0, 0, 5, 2.0)[0] == "silent"
    assert pt._verdict(0, 0, 0, 1, 2.0)[0] == "quiet - wait"
    assert pt._verdict(0, 0, 0, 2, 2.0)[0] == "watch"
    assert pt._verdict(10, 2, 5, 3, 5.0)[0] == "crowded-out"
    assert pt._verdict(10, 2, 0, 5, 5.0)[0] == "starved"     # 0.4/day < 25% of 5/day
    assert pt._verdict(10, 5, 0, 5, 1.0)[0] == "slow"        # 5/week < 15
    assert pt._verdict(40, 20, 0, 5, 5.0)[0] == "ok"         # 20/week


def test_expected_rates_from_config_notes(tmp_path):
    (tmp_path / "config").mkdir()
    (tmp_path / "config" / "default.yaml").write_text("strategies:\n  # plain note\n  A:\n    enabled: true\n")
    (tmp_path / "config" / "account_testing.yaml").write_text(
        "strategies:\n  # from A (primary); ~4.62/day full-day [x]\n  A-FD:\n    enabled: true\n  B:\n    enabled: true\n")
    exp = pt.expected_rates("testing", root=tmp_path)
    assert exp == {"A-FD": {"per_day": 4.62, "source": "config note"}}
    real = pt.expected_rates("testing")
    assert real["RW6G1-ns2-up3-vwap2sd-short-FD"]["per_day"] > 0 and real["NS1-rsidip-rsi5pop-long"]["per_day"] > 0


def test_eod_and_scorecard_carry_playing_time(tmp_path):
    j, run = _journal(tmp_path)
    st = _state(tmp_path)
    rep = pt.from_journal(j, run, "2026-10-09", {"account_name": "primary", "account": {"max_concurrent_positions": 160}}, st)
    page = eod.build(j, run, "2026-10-09", None, playing=rep)["html"]
    assert "Playing time — Primary account" in page and "NARROW" in page and "Educational only" in page
    card = scorecard.build(j.trades(run_id=run), 4, playing_time=rep)
    assert card["playing_time"]["cumulative"]["summary"]["lost_to_other_setups"] == 3
    assert "playing_time" not in scorecard.build(j.trades(run_id=run), 4)


def test_runner_logs_which_setup_holds_the_symbol(tmp_path, monkeypatch):
    """Logging only: the skip decision and reason are unchanged; info gains held_by."""
    from types import SimpleNamespace

    from mcf.strategies.base import Signal
    from tests.test_no_stacking import _runner

    r, b = _runner(tmp_path, monkeypatch)
    now = pd.Timestamp("2026-10-12 10:00:30", tz="America/New_York")
    ctx = SimpleNamespace(bars=pd.DataFrame({"volume": [1e6] * 5}), avg_dollar_volume=5e8)
    for name in ("NARROW", "WIDE"):
        r._enter(Signal("EDV", name, -1, 10, stop=55.0, target=54.0), 54.45, (name, "EDV"), ctx, now)
    assert len(b.submitted) == 1
    s = r.journal.signals(r.run_id, "2026-10-12")
    skip = s[s.strategy == "WIDE"].iloc[0]
    assert skip.status == "skipped" and skip.reason == "already in symbol"
    assert json.loads(skip["info"])["held_by"] == "NARROW"


def test_leaderboard_since_start_includes_untraded_live_setups():
    import pandas as pd
    from mcf.report import scorecard

    t = pd.DataFrame({"strategy": ["A"] * 4 + ["B"], "date": ["2026-10-06", "2026-10-07", "2026-10-08", "2026-10-09", "2026-10-09"],
                      "pnl": [10.0, -5.0, 8.0, 4.0, -3.0], "r_multiple": [1.0, -0.5, 0.8, 0.4, -0.3],
                      "entry_time": ["2026-10-06 10:00:00-04:00"] * 5})
    cfg = {"strategies": {"A": {"enabled": True}, "C": {"enabled": True, "former_primary": {"demoted": "2026-10-11"}},
                          "B": {"enabled": False}}}
    lb = {r["setup"]: r for r in scorecard.leaderboard(t, cfg, "testing")}
    assert lb["A"]["trades"] == 4 and lb["A"]["win_rate"] == 0.75 and lb["A"]["live"] and lb["A"]["account"] == "testing"
    assert lb["A"]["score"] == round(0.425 * 4 / 24, 4) and lb["A"]["profit_factor"] == round(22 / 5, 2)
    assert lb["C"]["trades"] == 0 and lb["C"]["score"] is None and lb["C"]["former_primary"]
    assert not lb["B"]["live"] and lb["B"]["trades"] == 1
    card = scorecard.build(t, 4, cfg=cfg, account="testing")
    assert len(card["leaderboard"]) == 3 and "generated" in card


def test_simulated_playing_time_kept_apart_from_live(tmp_path):
    """Owner 2026-10-13: what-if trades of signals not taken are reported per setup as SIMULATED sim_* fields,
    never mixed into live signals / entries / trades / win rate / P/L."""
    j, run = _journal(tmp_path)
    st = _state(tmp_path)
    wid = j.get_or_create_run("whatif", "MCF what-if (signals not taken)")
    d1, d2 = "2026-10-08", "2026-10-09"
    j.add_trades(wid, pd.DataFrame([
        {"symbol": "AAA", "strategy": "NARROW", "side": -1, "date": d1, "r_multiple": 1.0, "pnl": 0.0,
         "meta": "status=skipped;why=already in symbol"},
        {"symbol": "EEE", "strategy": "NARROW", "side": -1, "date": d2, "r_multiple": -0.5, "pnl": 0.0,
         "meta": "status=skipped;why=already in symbol"},
        {"symbol": "HHH", "strategy": "WIDE", "side": -1, "date": d2, "r_multiple": 0.3, "pnl": 0.0,
         "meta": "status=skipped;why=spread 40bps > max"},
    ]))
    cfg = {"account_name": "testing", "account": {"max_concurrent_positions": 400},
           "strategies": {"WIDE": {"enabled": True}, "NARROW": {"enabled": True}, "QUIET": {"enabled": True}},
           "live": {"setup_order": ["NARROW", "QUIET", "WIDE"]}}
    rep = pt.from_journal(j, run, d2, cfg, st)
    cum = {r["setup"]: r for r in rep["cumulative"]["setups"]}
    n = cum["NARROW"]
    assert n["entries"] == 1 and n["trades"] == 1 and n["signals"] == 4          # live counts unchanged
    assert n["sim_trades"] == 2 and n["sim_avg_r"] == 0.25 and n["sim_win_rate"] == 0.5
    assert n["sim_held_trades"] == 2 and n["sim_held_avg_r"] == 0.25
    assert cum["WIDE"]["sim_trades"] == 1 and cum["WIDE"]["sim_held_trades"] == 0 and cum["QUIET"]["sim_trades"] == 0
    assert rep["cumulative"]["summary"]["sim_trades"] == 3 and rep["cumulative"]["summary"]["trades"] == 3
    today = {r["setup"]: r for r in rep["today"]["setups"]}
    assert today["NARROW"]["sim_trades"] == 1 and rep["today"]["summary"]["sim_trades"] == 2
    assert "SIMULATED" in rep["sim_note"] and "SIMULATED" in pt.html(rep)
    card = scorecard.build(j.trades(run_id=run), 4, playing_time=rep, cfg=cfg, account="testing",
                           whatif=j.trades(kind="whatif"))
    lb = {r["setup"]: r for r in card["leaderboard"]}
    assert lb["NARROW"]["trades"] == 1 and lb["NARROW"]["avg_r"] == 0.2 and lb["NARROW"]["win_rate"] == 1.0
    assert lb["NARROW"]["sim_trades"] == 2 and lb["NARROW"]["sim_avg_r"] == 0.25 and lb["NARROW"]["sim_win_rate"] == 0.5
    assert lb["QUIET"]["sim_trades"] == 0 and lb["QUIET"]["sim_avg_r"] is None
    # no what-if run yet: zeros, not errors
    rep0 = pt.build(pd.DataFrame(columns=["day", "strategy", "status", "reason", "symbol"]), None, d2, cfg=cfg, expected={})
    assert rep0["cumulative"]["summary"]["sim_trades"] == 0
