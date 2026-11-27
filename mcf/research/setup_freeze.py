"""setup-freeze PR check (owner rule 2026-10-06, RESEARCH_RULES): setups, exits, sizing and risk rules may only change
outside market hours (09:30-16:00 ET, weekdays). Run by .github/workflows/setup-freeze.yml on every pull request.

What counts as a setup / rule change (a PR touching any of it fails while the market is open; after hours it passes):
  * any file under mcf/strategies/ or research/heat/candidates/ (as before);
  * config/default.yaml: the parsed value of a trading block - strategies, exits, shorts, live, universe (as before)
    and, since OPS-FREEZE (inspector 11-27), risk (latch / scaled halt / SHOCK-V / netbeta), account (sizing, slots,
    daily loss stops), costs (live cost model and the cost filter) and session (open / close / flatten timing);
  * config/account_*.yaml (OPS-FREEZE): any change of the parsed file - setup moves, per-account sizing, stops and
    exits live there - including an added or removed account file;
  * config/longhold.yaml (OPS-FREEZE): the S6 long-hold runner config, "frozen per session like setups" by its header.
Comment-only / formatting edits of the YAML files do not count (the parsed values are compared).

The window stays the fixed 09:30-16:00 ET weekdays (also on half days and holidays: never loosened by the calendar).
Stdlib + PyYAML only (the workflow runs it with the runner's python3, no pip install). Educational only - not
financial advice.
"""

from __future__ import annotations

import argparse
import glob
import os
import subprocess
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

import yaml

NY = ZoneInfo("America/New_York")
WATCH_DIRS = ("mcf/strategies", "research/heat/candidates")
DEFAULT_KEYS = ("strategies", "exits", "shorts", "live", "universe", "risk", "account", "costs", "session")
WATCH_FILES = ("config/longhold.yaml",)
ACCOUNT_GLOB = "config/account_*.yaml"
WINDOW = ("0930", "1600")                         # ET, weekdays; fixed (no calendar)


def _git(*args: str) -> str:
    return subprocess.run(["git", *args], capture_output=True, text=True).stdout


def _load(text: str | None):
    return (yaml.safe_load(text) if text else None) or {}


def show(base: str, path: str) -> str | None:
    """The file at the base commit, or None when it did not exist there."""
    r = subprocess.run(["git", "show", f"{base}:{path}"], capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else None


def read(path: str) -> str | None:
    return open(path).read() if os.path.exists(path) else None


def setup_changes(changed_files: list[str], old, new, account_paths: list[str]) -> list[str]:
    """Reasons this diff changes a setup / trading rule ([] = none).

    `old(path)` / `new(path)` return the file text at the base / in the PR (None = absent); `account_paths` is every
    config/account_*.yaml path present at the base or in the PR."""
    out = [f for f in changed_files if any(f == d or f.startswith(d + "/") for d in WATCH_DIRS)]
    o, n = _load(old("config/default.yaml")), _load(new("config/default.yaml"))
    keys = [k for k in DEFAULT_KEYS if o.get(k) != n.get(k)]
    if keys:
        out.append("config/default.yaml: " + ",".join(keys))
    for p in sorted(set(account_paths) | set(WATCH_FILES)):
        a, b = old(p), new(p)
        if a is None and b is None:
            continue
        if a is None or b is None:
            out.append(f"{p}: {'added' if a is None else 'removed'}")
        elif _load(a) != _load(b):
            out.append(p)
    return out


def frozen(now_et: datetime) -> bool:
    hm = now_et.strftime("%H%M")
    return now_et.weekday() < 5 and WINDOW[0] <= hm < WINDOW[1]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="setup-freeze PR check. Educational only.")
    ap.add_argument("--base", required=True, help="the PR base commit")
    a = ap.parse_args(argv)
    files = [f for f in _git("diff", "--name-only", f"{a.base}...HEAD").splitlines() if f]
    accounts = set(glob.glob(ACCOUNT_GLOB))
    accounts |= {p for p in _git("ls-tree", "--name-only", a.base, "config/").splitlines()
                 if p.startswith("config/account_") and p.endswith(".yaml")}
    reasons = setup_changes(files, lambda p: show(a.base, p), read, sorted(accounts))
    if not reasons:
        print("no setup changes")
        return 0
    print("setup changes: " + "; ".join(reasons))
    now = datetime.now(NY)
    if frozen(now):
        print("::error::Setup changes may only be merged outside market hours (09:30-16:00 ET). Merge after the close.")
        return 1
    print("outside market hours: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
