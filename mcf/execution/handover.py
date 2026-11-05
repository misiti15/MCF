"""Hand-over without GitHub cron (owner 2026-11-05). Educational only - not financial advice.

On 2026-11-05 GitHub fired NO scheduled run of any workflow in this repo from ~14:40 to ~19:50 UTC (09:40-14:50 ET):
trade.yml's hourly standbys, session-guard, watchdog and hunch's 09:40 start were all missing. The 08:48 ET trade run hit
the 355-min job limit at 14:40 ET with no standby queued behind it, and all 7 accounts had no session until a manual
dispatch at 14:49 ET. Every safety net was a cron line, so one scheduler outage beat all of them.

This module lets a running job start its own successor with workflow_dispatch (GITHUB_TOKEN, `actions: write`; a
workflow_dispatch made with GITHUB_TOKEN does start a run), so a hand-over no longer depends on cron:

  * trade.yml - each account's job starts `handover trade --account X --wait-until <job start + 340 min>` in the
    background of its Trade step. At that moment, if the job's own 355-min limit falls before 15:50 ET and no other
    trade run has a queued/pending job for this account, it dispatches trade.yml once. The new run's job waits in the
    account's concurrency group and starts the moment the old job ends. Accounts are staggered (30 s each) and re-check
    before dispatching, so 7 jobs ending together send one dispatch.
  * hunch.yml  - after the shadow loop exits (its 340-min cap or a crash) before 15:55 ET, it dispatches hunch.yml
    unless a hunch run is already queued.
  * watchdog.yml (job hunch-start) - on trading days 09:45-15:50 ET it dispatches hunch.yml when no hunch run is queued
    or in progress.

Caps: trade.yml shares session_guard.MAX_DISPATCHES (bot dispatches of trade.yml per day); hunch.yml at most
HUNCH_MAX_DISPATCHES bot dispatches a day. GitHub API only; no orders, no broker calls, no trading config touched."""

from __future__ import annotations

import argparse
import json
import os
import time as _time
import urllib.parse
from datetime import time

import pandas as pd

from mcf.execution import session_guard as sg

NY = sg.NY
ACTIVE = sg.ACTIVE
TRADE_END = time(15, 50)            # mcf live stops polling at 15:50 ET (trade.yml window check)
HUNCH_WINDOW = (time(9, 45), time(15, 50))   # watchdog start check (owner 2026-11-05)
HUNCH_RELAY_END = time(15, 55)      # after this a hunch successor has nothing left to guess
HUNCH_MAX_DISPATCHES = 4
STAGGER_S = 30


def bot_dispatches(runs: list[dict]) -> int:
    return sum(1 for r in runs if r.get("event") == "workflow_dispatch"
               and (r.get("triggering_actor") or {}).get("login") == "github-actions[bot]")


def account_covered(account: str, runs: list[dict], jobs: dict, own_run_id) -> bool:
    """True when a trade run other than our own will run `account` after us: a queued run with no jobs yet, or a job
    for the account that is queued / pending / waiting (in_progress elsewhere also counts - then we are the duplicate)."""
    for r in runs:
        if r.get("id") == own_run_id or r.get("status") not in ACTIVE:
            continue
        js = jobs.get(r.get("id"))
        if not js:
            return True
        for j in js:
            name = j.get("name", "")
            acct = name[name.find("(") + 1:name.rfind(")")] if "(" in name else ""
            if acct == account and j.get("status") in ACTIVE:
                return True
    return False


def decide_trade(now: pd.Timestamp, job_end: pd.Timestamp, account: str, runs: list[dict], jobs: dict, own_run_id,
                 dispatches_today: int) -> dict:
    """Pure: should this account's job dispatch its successor now? job_end = when the 355-min limit kills it."""
    now, job_end = now.tz_convert(NY), job_end.tz_convert(NY)
    out = {"at": str(now), "account": account, "job_end": str(job_end), "action": "none", "reasons": []}
    if now.weekday() >= 5:
        out["reasons"].append("weekend")
    elif job_end.date() != now.date() or job_end.time() >= TRADE_END:
        out["reasons"].append("job limit falls after 15:50 ET: no successor needed")
    elif account_covered(account, runs, jobs, own_run_id):
        out["reasons"].append("a successor is already queued")
    elif dispatches_today >= sg.MAX_DISPATCHES:
        out["action"] = "capped"
        out["reasons"].append(f"{dispatches_today} bot dispatches of trade.yml today (cap {sg.MAX_DISPATCHES})")
    else:
        out["action"] = "dispatch"
        out["reasons"].append(f"job limit at {job_end:%H:%M} ET and no trade run queued for {account}")
    return out


def decide_hunch(now: pd.Timestamp, market_open_today: bool, runs: list[dict], dispatches_today: int,
                 own_run_id=None, window=HUNCH_WINDOW) -> dict:
    """Pure: dispatch hunch.yml when no hunch run (other than our own) is queued or in progress."""
    now = now.tz_convert(NY)
    out = {"at": str(now), "action": "none", "reasons": []}
    if now.weekday() >= 5 or not (window[0] <= now.time() < window[1]):
        out["reasons"].append(f"outside {window[0]:%H:%M}-{window[1]:%H:%M} ET weekdays")
    elif not market_open_today:
        out["reasons"].append("not a market day")
    elif any(r.get("status") in ACTIVE and r.get("id") != own_run_id for r in runs):
        out["reasons"].append("a hunch run is queued or in progress")
    elif dispatches_today >= HUNCH_MAX_DISPATCHES:
        out["action"] = "capped"
        out["reasons"].append(f"{dispatches_today} bot dispatches of hunch.yml today (cap {HUNCH_MAX_DISPATCHES})")
    else:
        out["action"] = "dispatch"
        out["reasons"].append("no hunch run queued or in progress")
    return out


def _runs_today(workflow: str, now: pd.Timestamp) -> list[dict]:
    since = pd.Timestamp(now.tz_convert(NY).strftime("%Y-%m-%d"), tz=NY).tz_convert("UTC").strftime("%Y-%m-%dT%H:%M:%SZ")
    q = urllib.parse.quote(">=" + since)
    return (sg._gh(f"/actions/workflows/{workflow}/runs?per_page=100&created={q}") or {}).get("workflow_runs", [])


def _ref(ref: str | None) -> str:
    return ref or (sg._gh("") or {}).get("default_branch") or "main"


def _dispatch(workflow: str, ref: str, inputs: dict | None = None) -> None:
    sg._gh(f"/actions/workflows/{workflow}/dispatches", "POST", {"ref": ref, **({"inputs": inputs} if inputs else {})})


def run_trade(account: str, job_start: int, limit_min: int, lead_min: int, ref: str | None, mode: str) -> dict:
    job_end = pd.Timestamp(job_start + limit_min * 60, unit="s", tz="UTC")
    wake = job_start + (limit_min - lead_min) * 60
    idx = sg.ACCOUNTS.index(account) if account in sg.ACCOUNTS else 0
    delay = wake - _time.time() + idx * STAGGER_S
    if delay > 0:
        print(f"handover {account}: sleeping {delay / 60:.0f} min (job limit {job_end.tz_convert(NY):%H:%M} ET)", flush=True)
        _time.sleep(delay)
    now = pd.Timestamp.now(tz=NY)
    runs = _runs_today("trade.yml", now)
    jobs = {r["id"]: (sg._gh(f"/actions/runs/{r['id']}/jobs?per_page=50") or {}).get("jobs", [])
            for r in runs if r.get("status") in ACTIVE and r.get("id") != int(os.environ.get("GITHUB_RUN_ID", "0"))}
    d = decide_trade(now, job_end, account, runs, jobs, int(os.environ.get("GITHUB_RUN_ID", "0")), bot_dispatches(runs))
    d["mode"] = mode
    if d["action"] == "dispatch" and mode == "act":
        _dispatch("trade.yml", _ref(ref), {"dry_run": "false"})
        d["dispatched"] = True
    print("handover " + json.dumps(d, default=str), flush=True)
    return d


def run_hunch(ref: str | None, mode: str, relay: bool) -> dict:
    now = pd.Timestamp.now(tz=NY)
    runs = _runs_today("hunch.yml", now)
    own = int(os.environ.get("GITHUB_RUN_ID", "0")) if relay else None
    window = (time(9, 0), HUNCH_RELAY_END) if relay else HUNCH_WINDOW
    d = decide_hunch(now, sg.market_open_today(now.strftime("%Y-%m-%d")), runs, bot_dispatches(runs), own, window)
    d["mode"] = mode
    if d["action"] == "dispatch" and mode == "act":
        _dispatch("hunch.yml", _ref(ref))
        d["dispatched"] = True
    print("handover " + json.dumps(d, default=str), flush=True)
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a") as f:
            f.write("## Hunch start check\n\n" + f"- at: {d['at']}\n- action: **{d['action']}**"
                    + (" (sent)" if d.get("dispatched") else "") + "\n" + "".join(f"- {r}\n" for r in d["reasons"])
                    + "\n_Educational only - not financial advice._\n")
    return d


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    t = sub.add_parser("trade", help="sleep until near the job limit, then dispatch a successor trade run if needed")
    t.add_argument("--account", required=True)
    t.add_argument("--job-start", type=int, required=True, help="epoch seconds when the job started")
    t.add_argument("--limit-min", type=int, default=355)
    t.add_argument("--lead-min", type=int, default=15)
    h = sub.add_parser("hunch", help="dispatch hunch.yml when no hunch run is queued / in progress")
    h.add_argument("--relay", action="store_true", help="called from a hunch run that is ending (ignore own run)")
    for p in (t, h):
        p.add_argument("--ref", default=None, help="branch to dispatch on (default: the repo's default branch)")
        p.add_argument("--mode", default="act", choices=["dry", "act"])
    a = ap.parse_args(argv)
    try:
        if a.cmd == "trade":
            return run_trade(a.account, a.job_start, a.limit_min, a.lead_min, a.ref, a.mode)
        return run_hunch(a.ref, a.mode, a.relay)
    except Exception as e:  # noqa: BLE001 - a hand-over hiccup must never fail the trading / research job
        print(f"::warning::handover {a.cmd} failed: {e}")
        return {"action": "error", "error": str(e)}


if __name__ == "__main__":
    main()
