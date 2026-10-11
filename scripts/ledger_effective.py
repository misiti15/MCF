"""Fill the `effective` session date of research/ledger.jsonl entries that lack one.

An entry is effective from the first regular session that opens (09:30 ET, weekdays) after its line first appears
on the trading branch. The dashboard's "Changes for the next session" panel reads this field.
Usage: python scripts/ledger_effective.py [--branch origin/claude/intraday-trading-system-witis4]
Educational only - not financial advice.
"""
import argparse
import json
import subprocess
from datetime import datetime, time, timedelta
from pathlib import Path

LEDGER = Path(__file__).resolve().parents[1] / "research" / "ledger.jsonl"


def session_from(ts: datetime) -> str:
    """Landing during a session (owner-directed mid-session change) counts for that session."""
    d = ts.date()
    if ts.time() >= time(16, 0) or d.weekday() >= 5:
        d += timedelta(days=1)
    while d.weekday() >= 5:
        d += timedelta(days=1)
    return d.isoformat()


def landed(entry_id: str, branch: str) -> datetime | None:
    out = subprocess.run(["git", "log", branch, "--reverse", "--format=%cI", f'-S"{entry_id}"', "--", str(LEDGER)],
                         capture_output=True, text=True, cwd=LEDGER.parents[1]).stdout.split()
    if not out:
        return None
    ts = datetime.fromisoformat(out[0])
    return ts.astimezone(_et()).replace(tzinfo=None)


def _et():
    from zoneinfo import ZoneInfo
    return ZoneInfo("America/New_York")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--branch", default="origin/claude/intraday-trading-system-witis4")
    a = ap.parse_args()
    es = [json.loads(l) for l in LEDGER.read_text().splitlines() if l.strip()]
    for e in es:
        if e.get("effective"):
            continue
        ts = landed(e["id"], a.branch)
        if ts:
            e["effective"] = session_from(ts)
            e["landed"] = ts.strftime("%Y-%m-%d %H:%M ET")
            if ts.weekday() < 5 and time(9, 30) <= ts.time() < time(16, 0):
                e["mid_session"] = True
            print(e["id"], e["landed"], "->", e["effective"])
    LEDGER.write_text("".join(json.dumps(x) + "\n" for x in es))


if __name__ == "__main__":
    main()
