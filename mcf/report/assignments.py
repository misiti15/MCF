"""Setup assignments for the dashboard (owner 2026-10-20): which account(s) each setup is live in RIGHT NOW, straight
from the configs, with the time of the last promotion / demotion / move. The leaderboard uses this instead of the
`live` flags of last night's scorecards, so a move shows at once.

    python -m mcf.report.assignments            # rewrite docs/live/assignments.json (keeps earlier 'since' times)
    python -m mcf.report.assignments --at "2026-10-22 16:00"   # stamp the change at the time it takes effect (ET),
                                                 # e.g. a move prepared in market hours and merged after the close

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
ACCOUNTS = {"primary": "Primary", "testing": "Testing 1", "testing2": "Testing 2", "gen": "Setup Generator"}
if (ROOT / "config" / "account_graveyard.yaml").exists():      # the Graveyard account, once it exists
    ACCOUNTS["graveyard"] = "Graveyard"
# Split copies (owner 2026-10-20, "Goals for copies"): the only accounts where one setup may run twice, each copy on
# its own half of the tickers (ticker_split). Never Primary, Graveyard or the Setup Generator.
SPLIT_ACCOUNTS = ("testing", "testing2")


def _strategies() -> dict[str, dict]:
    """account -> its merged `strategies` block, exactly as the live runner loads it (default.yaml + account overlay)."""
    from ..config import load_config

    old = os.environ.get("MCF_ACCOUNT")
    out = {}
    try:
        for a in ACCOUNTS:
            os.environ["MCF_ACCOUNT"] = a
            out[a] = load_config().get("strategies") or {}
    finally:
        if old is None:
            os.environ.pop("MCF_ACCOUNT", None)
        else:
            os.environ["MCF_ACCOUNT"] = old
    return out


def current(strategies: dict | None = None) -> dict[str, list[str]]:
    """account -> sorted enabled setups, exactly as the live runner loads them (default.yaml + account overlay)."""
    strategies = strategies if strategies is not None else _strategies()
    return {a: sorted(k for k, v in st.items() if isinstance(v, dict) and v.get("enabled")) for a, st in strategies.items()}


def splits(strategies: dict | None = None) -> dict[str, dict[str, dict]]:
    """setup -> {account: {part, of}} for enabled split copies (ticker_split, owner 2026-10-20 'Goals for copies')."""
    strategies = strategies if strategies is not None else _strategies()
    out: dict[str, dict[str, dict]] = {}
    for a, st in strategies.items():
        for k, v in st.items():
            if isinstance(v, dict) and v.get("enabled") and v.get("ticker_split"):
                ts = v["ticker_split"]
                out.setdefault(k, {})[a] = {"part": int(ts["part"]), "of": int(ts["of"])}
    return out


def build(prev: dict | None = None, now: datetime | None = None) -> dict:
    now = now or datetime.now(ZoneInfo("America/New_York"))
    stamp = now.strftime("%Y-%m-%d %H:%M ET")
    strat = _strategies()
    acc = current(strat)
    split = splits(strat)
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
        if name in split:
            # split copies: one setup in both testing accounts, each on its own half of the tickers (stats combined)
            setups[name]["split"] = split[name]
    last = prev.get("last_change")
    if changes:
        last = {"at": stamp, "changes": changes}
    return {"note": "Live setup assignments from the configs; updated with every promotion / demotion / move. "
                    "Educational only - not financial advice.",
            "accounts": acc, "labels": ACCOUNTS, "setups": setups, "last_change": last}


def write(seed: dict | None = None, now: datetime | None = None) -> dict:
    prev = json.loads(OUT.read_text()) if OUT.exists() else None
    d = build(prev, now)
    if seed:
        d.update(seed.get("top", {}))
        for k, v in (seed.get("setups") or {}).items():
            d["setups"].setdefault(k, {}).update(v)
    OUT.write_text(json.dumps(d, indent=1) + "\n")
    return d


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--at", help="effective time 'YYYY-MM-DD HH:MM' (ET) for the stamp; default now. A move stamped at "
                                 "or after 16:00 shows on the dashboard as taking effect the next session.")
    a = ap.parse_args()
    at = datetime.strptime(a.at, "%Y-%m-%d %H:%M").replace(tzinfo=ZoneInfo("America/New_York")) if a.at else None
    d = write(now=at)
    print(json.dumps(d.get("last_change"), indent=1))
    sys.exit(0)
