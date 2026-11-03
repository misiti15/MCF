"""Research running order (owner CAP1, 2026-11-03): one ordered list of research jobs, so the nightly research runs
the most important items first and never takes more than its share of the GitHub job slots.

research/queue.jsonl holds one JSON object per item, in running order:
  {"id", "title", "added_by", "added_at", "priority", "status", "est_jobs", optional "notes"}
  status    pending | running | done | dropped
  priority  0 = owner (front of the list), 1 = high, 2 = normal (default), 3 = low
  est_jobs  GitHub Actions jobs (matrix legs) the item needs when it runs
Running order = pending items by (priority, position in the file). An item the OWNER adds goes to the front of the
pending list (priority 0, inserted before every pending item); anyone else's item goes to the end of its priority.
`tonight()` takes pending items in that order while their est_jobs fit the night's budget
(`research_queue.max_jobs_per_night` in the config, default 6).

    python -m mcf.research.queue list
    python -m mcf.research.queue add "COMBO1: ..." --by owner [--id COMBO1] [--jobs 3] [--priority 1]
    python -m mcf.research.queue next [-n 3]          # next n pending items
    python -m mcf.research.queue tonight [--max-jobs 6]
    python -m mcf.research.queue done ID              # (also: running ID, drop ID)
Research only - never changes a setup. Educational only - not financial advice.
"""
from __future__ import annotations

import argparse
import json
import re
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
QUEUE = ROOT / "research" / "queue.jsonl"
STATUSES = ("pending", "running", "done", "dropped")
OWNER_PRIORITY, DEFAULT_PRIORITY = 0, 2
DEFAULT_MAX_JOBS = 6


def items(path: Path | None = None) -> list[dict]:
    p = path or QUEUE
    return [json.loads(l) for l in p.read_text().splitlines() if l.strip()] if p.exists() else []


def save(es: list[dict], path: Path | None = None) -> None:
    (path or QUEUE).write_text("".join(json.dumps(e) + "\n" for e in es))


def is_owner(by: str | None) -> bool:
    return str(by or "").strip().lower().startswith("owner")


def pending(es: list[dict] | None = None) -> list[dict]:
    es = items() if es is None else es
    pos = {id(e): i for i, e in enumerate(es)}
    return sorted((e for e in es if e.get("status", "pending") == "pending"),
                  key=lambda e: (int(e.get("priority", DEFAULT_PRIORITY)), pos[id(e)]))


def next(n: int = 1, es: list[dict] | None = None) -> list[dict]:   # noqa: A001 - the owner's name for it
    """The next n pending items in running order."""
    return pending(es)[:max(0, int(n))]


def max_jobs(cfg: dict | None = None) -> int:
    if cfg is None:
        try:
            from ..config import load_config

            cfg = load_config()
        except Exception:   # noqa: BLE001 - the default applies
            cfg = {}
    return int(((cfg or {}).get("research_queue") or {}).get("max_jobs_per_night") or DEFAULT_MAX_JOBS)


def tonight(limit: int | None = None, es: list[dict] | None = None) -> list[dict]:
    """Pending items in running order while their est_jobs fit the night's budget. An item bigger than the whole
    budget still runs when it is first in line (alone), so nothing waits forever."""
    budget = max_jobs() if limit is None else int(limit)
    out, used = [], 0
    for e in pending(es):
        j = max(1, int(e.get("est_jobs") or 1))
        if used + j <= budget or not out and j > budget:
            out.append(e)
            used += j
        if used >= budget:
            break
    return out


def _slug(title: str) -> str:
    m = re.match(r"\s*([A-Z][A-Z0-9-]{1,15})\s*:", title)
    return m.group(1) if m else re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")[:40]


def add(title: str, added_by: str = "claude", id: str | None = None, est_jobs: int = 1,   # noqa: A002
        priority: int | None = None, added_at: str | None = None, notes: str | None = None,
        path: Path | None = None) -> dict:
    es = items(path)
    iid = id or _slug(title)
    if any(e["id"] == iid for e in es):
        raise ValueError(f"queue item {iid} already exists")
    owner = is_owner(added_by)
    e = {"id": iid, "title": title, "added_by": added_by, "added_at": added_at or str(date.today()),
         "priority": OWNER_PRIORITY if owner and priority is None else (DEFAULT_PRIORITY if priority is None else int(priority)),
         "status": "pending", "est_jobs": max(1, int(est_jobs))}
    if notes:
        e["notes"] = notes
    if owner:   # owner items go to the FRONT of the pending list
        es.insert(_first_pending(es), e)
    else:
        es.append(e)
    save(es, path)
    return e


def _first_pending(es: list[dict]) -> int:
    for i, x in enumerate(es):
        if x.get("status", "pending") == "pending":
            return i
    return len(es)


def set_status(iid: str, status: str, path: Path | None = None) -> dict:
    if status not in STATUSES:
        raise ValueError(f"status must be one of {STATUSES}")
    es = items(path)
    e = [x for x in es if x["id"] == iid]
    if not e:
        raise KeyError(iid)
    e[0]["status"] = status
    if status in ("done", "dropped"):
        e[0]["closed_at"] = str(date.today())
    save(es, path)
    return e[0]


def _line(e: dict) -> str:
    return f"{e.get('status', 'pending'):<8} p{e.get('priority', DEFAULT_PRIORITY)} {e.get('est_jobs', 1)}j  {e['id']:<14} {e['title']}  ({e.get('added_by')} {e.get('added_at')})"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="python -m mcf.research.queue")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list")
    a = sub.add_parser("add")
    a.add_argument("title")
    a.add_argument("--by", default="claude")
    a.add_argument("--id")
    a.add_argument("--jobs", type=int, default=1)
    a.add_argument("--priority", type=int)
    a.add_argument("--notes")
    n = sub.add_parser("next")
    n.add_argument("-n", type=int, default=1)
    t = sub.add_parser("tonight")
    t.add_argument("--max-jobs", type=int)
    for c in ("running", "done", "drop"):
        sub.add_parser(c).add_argument("id")
    x = ap.parse_args(argv)
    if x.cmd == "list":
        for e in pending() + [e for e in items() if e.get("status", "pending") != "pending"]:
            print(_line(e))
    elif x.cmd == "add":
        print(_line(add(x.title, x.by, x.id, x.jobs, x.priority, notes=x.notes)))
    elif x.cmd == "next":
        for e in next(x.n):
            print(_line(e))
    elif x.cmd == "tonight":
        lim = x.max_jobs if x.max_jobs is not None else max_jobs()
        sel = tonight(lim)
        print(f"tonight: {len(sel)} item(s), {sum(max(1, int(e.get('est_jobs') or 1)) for e in sel)} of {lim} jobs")
        for e in sel:
            print(_line(e))
    else:
        print(_line(set_status(x.id, {"drop": "dropped"}.get(x.cmd, x.cmd))))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
