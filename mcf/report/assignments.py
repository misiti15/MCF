"""Setup assignments for the dashboard (owner 2026-10-20): which account(s) each setup is live in RIGHT NOW, straight
from the configs, with the time of the last promotion / demotion / move. The leaderboard uses this instead of the
`live` flags of last night's scorecards, so a move shows at once.

    python -m mcf.report.assignments            # rewrite docs/live/assignments.json (keeps earlier 'since' times)

tests/test_assignments.py fails when docs/live/assignments.json does not match the configs, so every config change
that moves a setup must regenerate it in the same commit. Educational only - not financial advice.
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs" / "live" / "assignments.json"
ACCOUNTS = {"primary": "Primary", "testing": "Testing 1", "testing2": "Testing 2 (Graveyard)", "gen": "Setup Generator"}


def current() -> dict[str, list[str]]:
    """account -> sorted enabled setups, exactly as the live runner loads them (default.yaml + account overlay)."""
    from ..config import load_config

    old = os.environ.get("MCF_ACCOUNT")
    out = {}
    try:
        for a in ACCOUNTS:
            os.environ["MCF_ACCOUNT"] = a
            st = load_config().get("strategies") or {}
            out[a] = sorted(k for k, v in st.items() if isinstance(v, dict) and v.get("enabled"))
    finally:
        if old is None:
            os.environ.pop("MCF_ACCOUNT", None)
        else:
            os.environ["MCF_ACCOUNT"] = old
    return out


def build(prev: dict | None = None, now: datetime | None = None) -> dict:
    now = now or datetime.now(ZoneInfo("America/New_York"))
    stamp = now.strftime("%Y-%m-%d %H:%M ET")
    acc = current()
    prev = prev or {}
    pset = {k: set(v.get("accounts", [])) for k, v in (prev.get("setups") or {}).items()}
    setups, changes = {}, []
    for name in sorted({s for v in acc.values() for s in v} | set(pset)):
        here = sorted(a for a, v in acc.items() if name in v)
        before = pset.get(name)
        old = (prev.get("setups") or {}).get(name) or {}
        if before is None or before != set(here):
            since = stamp if prev else old.get("since")
            if prev:
                changes.append({"setup": name, "from": sorted(before or []), "to": here})
            setups[name] = {"accounts": here, "since": since, "from": sorted(before) if before else old.get("from")}
        else:
            setups[name] = {"accounts": here, "since": old.get("since"), "from": old.get("from")}
    last = prev.get("last_change")
    if changes:
        last = {"at": stamp, "changes": changes}
    return {"note": "Live setup assignments from the configs; updated with every promotion / demotion / move. "
                    "Educational only - not financial advice.",
            "accounts": acc, "labels": ACCOUNTS, "setups": setups, "last_change": last}


def write(seed: dict | None = None) -> dict:
    prev = json.loads(OUT.read_text()) if OUT.exists() else None
    d = build(prev)
    if seed:
        d.update(seed.get("top", {}))
        for k, v in (seed.get("setups") or {}).items():
            d["setups"].setdefault(k, {}).update(v)
    OUT.write_text(json.dumps(d, indent=1) + "\n")
    return d


if __name__ == "__main__":
    d = write()
    print(json.dumps(d.get("last_change"), indent=1))
    sys.exit(0)
