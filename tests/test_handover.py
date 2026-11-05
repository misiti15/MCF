"""Hand-over without GitHub cron (owner 2026-11-05). Educational only — not financial advice."""
from pathlib import Path

import pandas as pd
import yaml

from mcf.execution import handover as ho
from mcf.execution import session_guard as sg

WF = Path(__file__).resolve().parents[1] / ".github" / "workflows"


def at(hm, day="2026-11-05"):
    return pd.Timestamp(f"{day} {hm}", tz="America/New_York")


def job(acct, status):
    return {"name": f"session ({acct})", "status": status}


def test_the_11_05_case_dispatches_a_successor():
    # 08:48 job, limit 14:43 ET, no standby queued (cron outage): dispatch at 14:28
    runs = [{"id": 1, "status": "in_progress"}]
    d = ho.decide_trade(at("14:28"), at("14:43"), "primary", runs, {1: [job("primary", "in_progress")]}, 1, 0)
    assert d["action"] == "dispatch"


def test_queued_standby_or_fresh_dispatch_means_no_duplicate():
    own = {"id": 1, "status": "in_progress"}
    assert ho.decide_trade(at("14:28"), at("14:43"), "gen", [own, {"id": 2, "status": "queued"}], {}, 1, 0)["action"] == "none"
    js = {2: [job("gen", "pending"), job("primary", "pending")]}
    assert ho.decide_trade(at("14:28"), at("14:43"), "gen", [own, {"id": 2, "status": "in_progress"}], js, 1, 0)["action"] == "none"
    # another run that only covers a different account does not count
    js = {2: [job("primary", "pending"), job("gen", "completed")]}
    assert ho.decide_trade(at("14:28"), at("14:43"), "gen", [own, {"id": 2, "status": "in_progress"}], js, 1, 0)["action"] == "dispatch"


def test_no_successor_after_the_close_weekend_or_cap():
    assert ho.decide_trade(at("15:40"), at("15:55"), "primary", [], {}, 1, 0)["action"] == "none"
    assert ho.decide_trade(at("10:00", "2026-11-07"), at("10:15", "2026-11-07"), "primary", [], {}, 1, 0)["action"] == "none"
    assert ho.decide_trade(at("14:28"), at("14:43"), "primary", [], {}, 1, sg.MAX_DISPATCHES)["action"] == "capped"


def test_hunch_start_check():
    assert ho.decide_hunch(at("09:50"), True, [], 0)["action"] == "dispatch"            # 11-05: 09:40 start never fired
    assert ho.decide_hunch(at("09:40"), True, [], 0)["action"] == "none"                # before 09:45
    assert ho.decide_hunch(at("15:50"), True, [], 0)["action"] == "none"
    assert ho.decide_hunch(at("10:00"), False, [], 0)["action"] == "none"               # holiday
    assert ho.decide_hunch(at("10:00"), True, [{"id": 5, "status": "in_progress"}], 0)["action"] == "none"
    assert ho.decide_hunch(at("10:00"), True, [{"id": 5, "status": "queued"}], 0)["action"] == "none"
    assert ho.decide_hunch(at("10:00"), True, [], ho.HUNCH_MAX_DISPATCHES)["action"] == "capped"
    # relay from the ending run ignores itself
    d = ho.decide_hunch(at("15:30"), True, [{"id": 5, "status": "in_progress"}], 0, own_run_id=5,
                        window=(ho.time(9, 0), ho.HUNCH_RELAY_END))
    assert d["action"] == "dispatch"


def test_bot_dispatch_count():
    runs = [{"event": "workflow_dispatch", "triggering_actor": {"login": "github-actions[bot]"}},
            {"event": "workflow_dispatch", "triggering_actor": {"login": "misiti15"}}, {"event": "schedule"}]
    assert ho.bot_dispatches(runs) == 1


def test_trade_workflow_dispatches_its_own_successor():
    wf = yaml.safe_load((WF / "trade.yml").read_text())
    assert wf["permissions"]["actions"] == "write"
    job_ = wf["jobs"]["session"]
    assert job_["timeout-minutes"] == 355
    trade = next(s for s in job_["steps"] if s.get("name") == "Trade")
    assert "mcf.execution.handover trade" in trade["run"] and "&" in trade["run"]
    assert trade["env"]["GITHUB_TOKEN"] == "${{ github.token }}"
    assert "MCF_JOB_T0" in next(s for s in job_["steps"] if s.get("name") == "Window check")["run"]


def test_hunch_workflow_hands_over_and_watchdog_starts_it():
    wf = yaml.safe_load((WF / "hunch.yml").read_text())
    assert wf["permissions"]["actions"] == "write"
    steps = wf["jobs"]["shadow"]["steps"]
    i = next(k for k, s in enumerate(steps) if "handover hunch --relay" in s.get("run", ""))
    assert steps[i]["if"].startswith("always()")
    wd = yaml.safe_load((WF / "watchdog.yml").read_text())
    hs = wd["jobs"]["hunch-start"]
    assert hs["permissions"]["actions"] == "write"
    assert "strategy" not in hs                                       # one job, not per account
    run = "\n".join(s.get("run", "") for s in hs["steps"])
    assert "mcf.execution.handover hunch" in run and "0945" in run and "1550" in run
    assert "ALPACA_TRADE_API_KEY" not in hs.get("env", {})            # no trading keys
