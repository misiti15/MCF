"""Kill switch (LR4, owner 2026-11-11): stop new entries, or flatten, on one account or all, without cancelling runs.

The flag is one JSON file, HALT.json, on the branch `mcf-control` (written only by the manual workflow kill.yml):
  {"accounts": {"primary": {"mode": "entries" | "flatten", "at": ISO time, "by": actor}, "all": {...}}}
Every trading run reads it on every poll (PaperRunner._kill_check: `git ls-remote` on its state checkout, a fetch only
when the branch moved; a local file MCF_HALT_FILE overrides it for tests / local runs):
  entries  -> no new entries for the rest of the session; open lots keep their broker-side stops and targets
  flatten  -> the same, and the run cancels its MCF orders and closes its MCF positions once (per flag)
kill.yml with mode "flatten" ALSO flattens directly from its own job (no trading run needed), through the same broker
code as the runner / watchdog (outage.flatten_prefix: this account's order prefix only; nothing else on the account is
touched). Mode "resume" clears the account's flag (and "all" clears every flag). A read error keeps the last known
flag in a run. Educational only - not financial advice.

    python -m mcf.execution.kill set --account primary --mode entries [--dry-run]
    python -m mcf.execution.kill flatten [--dry-run]     # MCF_COID_PREFIX / account keys from the environment
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import tempfile
import urllib.error
import urllib.request
from pathlib import Path

import pandas as pd

BRANCH = "mcf-control"
FILE = "HALT.json"
MODES = {"no-new-entries": "entries", "entries": "entries", "flatten": "flatten", "resume": "resume"}
NY = "America/New_York"


_last: dict = {"sha": None, "flags": {}}


def read_flag(git_dir: str | None = None) -> dict | None:
    """{"accounts": {...}} from MCF_HALT_FILE, else from the mcf-control branch; {} when no flag is set (file / branch
    missing, or nowhere to read from); None when the flag could not be read (the run keeps its last known state).

    The branch is read with git, not the REST API (10 accounts polling every minute would use most of GITHUB_TOKEN's
    1,000 requests/hour): `git ls-remote` every check (~1 s), and a depth-1 fetch only when the branch head moved.
    git_dir: a clone whose `origin` is this repository (the run's state checkout); without it, the GitHub contents
    API is used once per call (kill.yml / tools)."""
    path = os.environ.get("MCF_HALT_FILE")
    if path:
        p = Path(path)
        if not p.exists():
            return {}
        try:
            return json.loads(p.read_text() or "{}")
        except ValueError:
            return None
    if git_dir and (Path(git_dir) / ".git").exists():
        r = _git(git_dir, "ls-remote", "origin", f"refs/heads/{BRANCH}")
        if r.returncode:
            return None
        sha = (r.stdout.split() or [None])[0]
        if sha is None:
            _last.update(sha=None, flags={})
            return {}
        if sha != _last["sha"]:
            if _git(git_dir, "fetch", "-q", "--depth", "1", "origin", f"{BRANCH}:refs/mcf/{BRANCH}").returncode:
                return None
            shown = _git(git_dir, "show", f"refs/mcf/{BRANCH}:{FILE}")
            try:
                flags = json.loads(shown.stdout or "{}") if shown.returncode == 0 else {}
            except ValueError:
                return None
            _last.update(sha=sha, flags=flags)
        return _last["flags"]
    repo, tok = os.environ.get("GITHUB_REPOSITORY"), os.environ.get("GITHUB_TOKEN")
    if not repo or not tok:
        return {}
    req = urllib.request.Request(f"https://api.github.com/repos/{repo}/contents/{FILE}?ref={BRANCH}",
                                 headers={"Authorization": f"Bearer {tok}", "Accept": "application/vnd.github.raw"})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        return {} if e.code == 404 else None
    except Exception:
        return None


def flag_for(flags: dict | None, account: str) -> dict | None:
    """The flag that applies to `account` (its own, else "all"); None when trading may go on."""
    acc = (flags or {}).get("accounts") or {}
    for k in (account, "all"):
        f = acc.get(k)
        if isinstance(f, dict) and f.get("mode") in ("entries", "flatten"):
            return {**f, "scope": k}
    return None


def update(flags: dict | None, account: str, mode: str, by: str = "owner", now: pd.Timestamp | None = None) -> dict:
    """Pure: the new HALT.json content after setting `mode` for `account` ("all" = every account)."""
    mode = MODES[mode]
    acc = dict((flags or {}).get("accounts") or {})
    if mode == "resume":
        if account == "all":
            acc = {}
        else:
            acc.pop(account, None)
    else:
        now = now if now is not None else pd.Timestamp.now(tz=NY)
        acc[account] = {"mode": mode, "at": now.tz_convert(NY).isoformat(timespec="seconds"), "by": by}
    return {"accounts": acc, "note": "Written by kill.yml (LR4). Educational only - not financial advice."}


def _git(d, *args) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(d), *args], capture_output=True, text=True)


def set_flag(account: str, mode: str, by: str, dry_run: bool = False) -> dict:
    """Write HALT.json on the mcf-control branch (created as an orphan branch on first use) and push it."""
    repo, tok = os.environ.get("GITHUB_REPOSITORY"), os.environ.get("GITHUB_TOKEN")
    current = read_flag() or {}
    new = update(current, account, mode, by)
    print(f"kill flag {account}: {MODES[mode]} -> {json.dumps(new['accounts'])}")
    if dry_run or not repo or not tok:
        print("dry run (or no GitHub context): flag not written")
        return new
    url = f"https://x-access-token:{tok}@github.com/{repo}.git"
    with tempfile.TemporaryDirectory() as d:
        if subprocess.run(["git", "clone", "-q", "--depth", "1", "--branch", BRANCH, url, d],
                          capture_output=True).returncode:
            _git(d, "init", "-q")
            _git(d, "checkout", "-q", "--orphan", BRANCH)
            _git(d, "remote", "add", "origin", url)
        (Path(d) / FILE).write_text(json.dumps(new, indent=1) + "\n")
        _git(d, "add", FILE)
        _git(d, "-c", "user.name=mcf-bot", "-c", "user.email=mcf-bot@users.noreply.github.com", "commit", "-q",
             "-m", f"kill switch: {account} {MODES[mode]} ({by})")
        r = _git(d, "push", "-q", "origin", f"HEAD:{BRANCH}")
        if r.returncode:
            raise SystemExit(f"push of {FILE} to {BRANCH} failed: {r.stderr.strip()[:200]}")
    return new


def flatten(prefix: str, broker=None, dry_run: bool = False, sleep=None) -> dict:
    """Cancel this account's MCF orders and close the positions on symbols it traded today (prefix only)."""
    from .outage import check_prefix, flatten_prefix, mcf_symbols_today

    check_prefix(prefix)
    if broker is None:
        from .alpaca_broker import AlpacaBroker

        broker = AlpacaBroker(paper=True)
    mine = mcf_symbols_today(broker, prefix)
    held = sorted(mine & set(broker.positions()))
    if dry_run:
        print(f"KILL (dry run) would cancel open {prefix}* orders and flatten {held}")
        return {"prefix": prefix, "dry_run": True, "would_flatten": held}
    left = flatten_prefix(broker, prefix, set(held), sleep=sleep)
    print(f"KILL flattened {prefix}*: {held}; still open: {left}")
    return {"prefix": prefix, "flattened": held, "left": left}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("set")
    s.add_argument("--account", required=True)
    s.add_argument("--mode", required=True, choices=sorted(MODES))
    s.add_argument("--by", default=os.environ.get("GITHUB_ACTOR", "owner"))
    s.add_argument("--dry-run", action="store_true")
    f = sub.add_parser("flatten")
    f.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    if a.cmd == "set":
        out = set_flag(a.account, a.mode, a.by, a.dry_run)
    else:
        out = flatten(os.environ.get("MCF_COID_PREFIX", "mcf-"), dry_run=a.dry_run)
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a") as fh:
            fh.write(f"### MCF kill switch ({a.cmd})\n\n```\n{json.dumps(out, indent=1, default=str)}\n```\n\n"
                     "*Educational only - not financial advice.*\n")
    return out


if __name__ == "__main__":
    main()
