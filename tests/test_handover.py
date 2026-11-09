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


# ---------------------------------------------------------------- HK-EOD-CHAIN (2026-11-09): EOD from the closing run
def eod_run(hm, status="completed", conclusion="success", event="workflow_run", day="2026-11-09"):
    return {"id": 90, "status": status, "conclusion": conclusion, "event": event,
            "created_at": at(hm, day).tz_convert("UTC").strftime("%Y-%m-%dT%H:%M:%SZ")}


def test_the_11_09_case_closing_run_starts_eod():
    # bot-dispatched closing run, no workflow_run chain, cron missed: eod-start dispatches eod.yml
    own = {"id": 1, "status": "in_progress"}
    d = ho.decide_eod(at("15:57", "2026-11-09"), True, [own], {}, 1, [eod_run("10:40")], 0)
    assert d["action"] == "dispatch"


def test_eod_start_waits_for_other_runs_and_is_idempotent():
    day, own = "2026-11-09", {"id": 1, "status": "in_progress"}
    now = at("15:57", day)
    # another trade run still has a session job running (or is queued with no jobs): its eod-start goes last
    other = {"id": 2, "status": "in_progress"}
    js = {2: [job("primary", "in_progress"), {"name": "eod-start", "status": "pending"}]}
    assert ho.decide_eod(now, True, [own, other], js, 1, [], 0)["action"] == "none"
    assert ho.decide_eod(now, True, [own, {"id": 2, "status": "queued"}], {}, 1, [], 0)["action"] == "none"
    # only its own eod-start job left in the other run -> no session job active -> dispatch
    js = {2: [job("primary", "completed"), {"name": "eod-start", "status": "in_progress"}]}
    assert ho.decide_eod(now, True, [own, other], js, 1, [], 0)["action"] == "dispatch"
    # EOD since the close already running or done (workflow_run chain / cron / earlier dispatch): no duplicate
    assert ho.decide_eod(now, True, [own], {}, 1, [eod_run("15:56", "in_progress", None)], 0)["action"] == "none"
    assert ho.decide_eod(now, True, [own], {}, 1, [eod_run("15:56")], 0)["action"] == "none"
    # a failed EOD after the close is retried; one from mid-day does not count
    assert ho.decide_eod(now, True, [own], {}, 1, [eod_run("15:56", conclusion="failure")], 0)["action"] == "dispatch"
    assert ho.decide_eod(now, True, [own], {}, 1, [], ho.EOD_MAX_DISPATCHES)["action"] == "capped"


def test_eod_start_only_after_the_close_on_market_days():
    assert ho.decide_eod(at("14:43", "2026-11-09"), True, [], {}, 1, [], 0)["action"] == "none"   # mid-day hand-over end
    assert ho.decide_eod(at("20:05", "2026-11-09"), True, [], {}, 1, [], 0)["action"] == "none"
    assert ho.decide_eod(at("16:00", "2026-11-07"), True, [], {}, 1, [], 0)["action"] == "none"   # Saturday
    assert ho.decide_eod(at("16:00", "2026-11-09"), False, [], {}, 1, [], 0)["action"] == "none"  # holiday


def test_run_eod_dispatches_with_auto(monkeypatch):
    sent = []
    monkeypatch.setattr(ho, "_runs_today", lambda wf, now: [])
    monkeypatch.setattr(ho.sg, "market_open_today", lambda day: True)
    monkeypatch.setattr(ho, "_dispatch", lambda wf, ref, inputs=None: sent.append((wf, ref, inputs)))
    monkeypatch.setattr(ho.pd.Timestamp, "now", classmethod(lambda cls, tz=None: at("15:58", "2026-11-09")))
    monkeypatch.delenv("GITHUB_STEP_SUMMARY", raising=False)
    assert ho.run_eod("main", "act")["dispatched"] is True
    assert sent == [("eod.yml", "main", {"auto": "true"})]
    sent.clear()
    assert "dispatched" not in ho.run_eod("main", "dry") and sent == []


def test_trade_workflow_starts_eod_and_eod_keeps_its_backups():
    tr = yaml.safe_load((WF / "trade.yml").read_text())
    es = tr["jobs"]["eod-start"]
    assert es["needs"] == "session" and es["if"] == "always()" and "strategy" not in es
    assert tr["permissions"]["actions"] == "write"
    run = "\n".join(s.get("run", "") for s in es["steps"])
    assert "mcf.execution.handover eod" in run and "1555" in run and "|| true" in run
    assert "ALPACA_TRADE_API_KEY" not in es.get("env", {})          # no trading keys in the dispatcher job
    eod = yaml.safe_load((WF / "eod.yml").read_text())
    on = eod[True] if True in eod else eod["on"]                       # PyYAML reads `on:` as True
    assert on["workflow_run"]["workflows"] == ["trade"] and on["schedule"]          # backups stay
    assert on["workflow_dispatch"]["inputs"]["auto"]["default"] is False
    w = next(s for s in eod["jobs"]["report"]["steps"] if s.get("name") == "Window check")["run"]
    assert "inputs.auto" in w and w.index("inputs.auto") < w.index('= "workflow_dispatch" ]; then run=true')
