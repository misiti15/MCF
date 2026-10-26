"""Session guard (owner 2026-10-26): start the trading session when GitHub's schedule did not.

On 2026-10-26 GitHub fired no scheduled run at all (trade.yml, watchdog.yml) and the session started by hand at 10:30 ET.
This guard runs from .github/workflows/session-guard.yml (many cron lines, plus workflow_dispatch so an outside caller -
the Claude scheduled task - can fire it when GitHub cron is down) and from that caller directly.

Rule: on a market day between 08:40 and 15:30 ET, every account with keys must have a trade.yml job that is queued or
in progress. If one does not (no run today, a crashed job, the 6-hour job limit hit and no standby run behind it), it
dispatches trade.yml. A second run is harmless: each account's job waits in its concurrency group behind a live one and
the live runner resumes from the state branch. At most MAX_DISPATCHES guard dispatches a day, so a job that dies at once
cannot loop. GitHub API (GITHUB_TOKEN) and the Alpaca calendar (GET only). Educational only - not financial advice."""

from __future__ import annotations

import argparse
import json
import os
import urllib.parse
import urllib.request
from datetime import time

import pandas as pd

NY = "America/New_York"
WINDOW = (time(8, 40), time(15, 30))
ACCOUNTS = ("primary", "testing", "testing2", "gen", "graveyard")
ACTIVE = {"queued", "in_progress", "waiting", "requested", "pending"}
MAX_DISPATCHES = 6
WORKFLOW = "trade.yml"
TITLE = "trade"


def _ts(s) -> pd.Timestamp:
    t = pd.Timestamp(s)
    return t.tz_localize("UTC") if t.tzinfo is None else t


def decide(now: pd.Timestamp, market_open_today: bool, runs: list[dict], jobs: dict, accounts: list[str],
           guard_dispatches_today: int) -> dict:
    """Pure decision. runs = trade.yml runs (id, status, created_at); jobs = {run_id: [{name, status}]}."""
    now = now.tz_convert(NY)
    out = {"at": str(now), "action": "none", "missing": [], "active_runs": [], "reasons": []}
    if now.weekday() >= 5 or not (WINDOW[0] <= now.time() < WINDOW[1]):
        out["note"] = "outside 08:40-15:30 ET weekdays"
        return out
    if not market_open_today:
        out["note"] = "not a market day (holiday)"
        return out
    covered = set()
    for r in runs:
        if r.get("status") not in ACTIVE:
            continue
        out["active_runs"].append(r.get("id"))
        js = jobs.get(r.get("id"))
        if not js:                       # run queued, jobs not created yet: counts for every account
            covered.update(accounts)
            continue
        for j in js:
            name = j.get("name", "")
            acct = name[name.find("(") + 1:name.rfind(")")] if "(" in name else ""
            if j.get("status") in ACTIVE and acct:
                covered.add(acct)
    out["missing"] = [a for a in accounts if a not in covered]
    if not out["missing"]:
        return out
    if guard_dispatches_today >= MAX_DISPATCHES:
        out["action"] = "capped"
        out["reasons"].append(f"{guard_dispatches_today} guard dispatches today (cap {MAX_DISPATCHES}): not dispatching")
        return out
    out["action"] = "dispatch"
    out["reasons"].append("no queued / running trade job for " + ", ".join(out["missing"]))
    return out


def _gh(path: str, method: str = "GET", body: dict | None = None):
    repo, tok = os.environ["GITHUB_REPOSITORY"], os.environ["GITHUB_TOKEN"]
    req = urllib.request.Request(f"https://api.github.com/repos/{repo}{path}", method=method,
                                 data=json.dumps(body).encode() if body is not None else None,
                                 headers={"Authorization": f"Bearer {tok}", "Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        raw = r.read()
    return json.loads(raw) if raw else None


def market_open_today(day: str) -> bool:
    """Alpaca trading calendar (GET only). Unreachable -> assume a market day (the runner itself exits on holidays)."""
    key, sec = os.environ.get("ALPACA_API_KEY"), os.environ.get("ALPACA_SECRET_KEY")
    if not key or not sec:
        return True
    req = urllib.request.Request(f"https://paper-api.alpaca.markets/v2/calendar?start={day}&end={day}",
                                 headers={"APCA-API-KEY-ID": key, "APCA-API-SECRET-KEY": sec})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            cal = json.loads(r.read())
        return any(c.get("date") == day for c in cal)
    except Exception as e:  # noqa: BLE001 - guard must not fail on a calendar hiccup
        print(f"calendar unreachable ({e}); assuming a market day")
        return True


def run(accounts: list[str], ref: str, mode: str) -> dict:
    now = pd.Timestamp.now(tz=NY)
    day = now.strftime("%Y-%m-%d")
    since = pd.Timestamp(day, tz=NY).tz_convert("UTC").strftime("%Y-%m-%dT%H:%M:%SZ")
    runs = (_gh(f"/actions/workflows/{WORKFLOW}/runs?per_page=50&created=" + urllib.parse.quote(">=" + since)) or {}).get("workflow_runs", [])
    jobs = {}
    for r in runs:
        if r.get("status") in ACTIVE:
            jobs[r["id"]] = (_gh(f"/actions/runs/{r['id']}/jobs?per_page=50") or {}).get("jobs", [])
    mine = sum(1 for r in runs if r.get("event") == "workflow_dispatch"
               and (r.get("triggering_actor") or {}).get("login") == "github-actions[bot]")
    d = decide(now, market_open_today(day), runs, jobs, accounts, mine)
    d["guard_dispatches_today"] = mine
    d["mode"] = mode
    if d["action"] == "dispatch" and mode == "act":
        _gh(f"/actions/workflows/{WORKFLOW}/dispatches", "POST", {"ref": ref, "inputs": {"dry_run": "false"}})
        d["dispatched"] = True
        print(f"dispatched {WORKFLOW} on {ref}: " + "; ".join(d["reasons"]))
    else:
        print(json.dumps(d, default=str))
    return d


def _summary(d: dict) -> str:
    lines = ["## Session guard", "", f"- at: {d['at']}", f"- action: **{d['action']}**" + (" (sent)" if d.get("dispatched") else "")]
    lines += [f"- {k}: {d[k]}" for k in ("note", "missing", "active_runs", "guard_dispatches_today") if d.get(k) not in (None, [])]
    lines += [f"- {r}" for r in d.get("reasons", [])]
    return "\n".join(lines + ["", "_Educational only - not financial advice._", ""])


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--accounts", default=",".join(ACCOUNTS), help="accounts whose keys are set (comma list)")
    ap.add_argument("--ref", default=os.environ.get("GITHUB_REF_NAME") or "main")
    ap.add_argument("--mode", default="act", choices=["dry", "act"])
    a = ap.parse_args(argv)
    d = run([x for x in a.accounts.split(",") if x], a.ref, a.mode)
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a") as f:
            f.write(_summary(d))
    return d


if __name__ == "__main__":
    main()
