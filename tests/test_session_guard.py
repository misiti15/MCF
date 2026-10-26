"""Session guard (owner 2026-10-26): dispatch trade.yml when GitHub's schedule did not start the session."""

import pandas as pd

from mcf.execution.session_guard import MAX_DISPATCHES, decide

ACC = ["primary", "testing", "testing2", "gen", "graveyard"]


def at(hm, day="2026-10-26"):
    return pd.Timestamp(f"{day} {hm}", tz="America/New_York")


def job(acct, status):
    return {"name": f"session ({acct})", "status": status}


def test_no_run_today_dispatches():                       # the 2026-10-26 case
    d = decide(at("10:28"), True, [], {}, ACC, 0)
    assert d["action"] == "dispatch" and d["missing"] == ACC


def test_all_running_no_action():
    runs = [{"id": 1, "status": "in_progress"}]
    d = decide(at("10:28"), True, runs, {1: [job(a, "in_progress") for a in ACC]}, ACC, 0)
    assert d["action"] == "none" and d["missing"] == []


def test_one_crashed_job_dispatches_for_it():
    runs = [{"id": 1, "status": "in_progress"}]
    js = [job(a, "in_progress") for a in ACC if a != "gen"] + [job("gen", "completed")]
    d = decide(at("11:00"), True, runs, {1: js}, ACC, 0)
    assert d["action"] == "dispatch" and d["missing"] == ["gen"]


def test_queued_standby_counts():
    runs = [{"id": 1, "status": "completed"}, {"id": 2, "status": "queued"}]
    d = decide(at("13:00"), True, runs, {2: []}, ACC, 0)
    assert d["action"] == "none"


def test_window_weekend_holiday_and_cap():
    assert decide(at("08:30"), True, [], {}, ACC, 0)["action"] == "none"
    assert decide(at("15:35"), True, [], {}, ACC, 0)["action"] == "none"
    assert decide(at("10:00", "2026-10-24"), True, [], {}, ACC, 0)["action"] == "none"     # Saturday
    assert decide(at("10:00", "2026-11-26"), False, [], {}, ACC, 0)["action"] == "none"    # Thanksgiving
    assert decide(at("10:00"), True, [], {}, ACC, MAX_DISPATCHES)["action"] == "capped"


def test_only_accounts_with_keys():
    runs = [{"id": 1, "status": "in_progress"}]
    d = decide(at("10:00"), True, runs, {1: [job("primary", "in_progress")]}, ["primary"], 0)
    assert d["action"] == "none"
