"""Arena reps in active days (owner C3-ROT yes 2026-11-18; research/consultant_p3/RESULTS.md #9). Report only.

Per setup, from the state branches (mcf-data-<account>):
  active_days   live sessions: the session's setup snapshot (setups/<date>.json) has the setup enabled (benched,
                away and family-capped sessions do not count) - the rep unit for every arena verdict
  traded_days   active days with >= 1 live trade (journal run 1)
  trades        live trades (run 1, closed)
  shadow_days   sessions with >= 1 shadow trade of the setup (journal run kind 'shadow') - a SEPARATE column, never
                added to the live record (SRCV1); it orders the rotation together with active_days
  signals / blocked_pct   live signals and the share skipped (any reason)
  verdict_ready true at >= 15 active days AND >= 30 trades (no verdicts before, bugs excepted)
  triage        "zero-signal" (0 signals in >= 10 active days) / "blocked" (>= 60% of >= 10 signals skipped):
                tagged, never disabled; listed every 2 sessions

    python -m mcf.report.arena_reps [--remote origin] [--until YYYY-MM-DD]   # writes docs/live/arena_reps.json

The rotation (mcf/rotation.py family_caps) reads active_days + shadow_days from that file. Educational only - not
financial advice.
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import subprocess
import tempfile
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs" / "live" / "arena_reps.json"
BRANCHES = {"primary": "mcf-data", "testing": "mcf-data-testing", "testing2": "mcf-data-testing2",
            "explore1": "mcf-data-explore1", "livelab": "mcf-data-livelab", "testingd": "mcf-data-testingd",
            "testinge": "mcf-data-testinge", "testingf": "mcf-data-testingf", "gen": "mcf-data-gen",
            "graveyard": "mcf-data-graveyard"}
MIN_DAYS, MIN_TRADES = 15, 30
TRIAGE_DAYS, BLOCKED_SHARE, BLOCKED_MIN = 10, 0.60, 10


def _git(*a) -> str:
    return subprocess.run(["git", "-C", str(ROOT), *a], capture_output=True, text=True).stdout


def build(snapshots: dict, journals: dict, until: str | None = None) -> dict:
    """snapshots: account -> {date: snapshot dict}; journals: account -> sqlite3 path. Pure (testable)."""
    act, trd, shd = defaultdict(set), defaultdict(set), defaultdict(set)
    n_tr, n_sig, n_skip = defaultdict(int), defaultdict(int), defaultdict(int)
    for acct, snaps in snapshots.items():
        for d, s in snaps.items():
            if until and d > until:
                continue
            for k, v in ((s or {}).get("strategies") or {}).items():
                if isinstance(v, dict) and v.get("enabled", True):
                    act[k].add(d)
    for acct, path in journals.items():
        c = sqlite3.connect(path)
        try:
            runs = dict(c.execute("SELECT id, kind FROM runs").fetchall())
            for rid, kind in runs.items():
                q = "SELECT strategy, date FROM trades WHERE run_id=? AND exit_time IS NOT NULL"
                for k, d in c.execute(q, (rid,)):
                    if until and str(d) > until:
                        continue
                    if rid == 1:
                        trd[k].add(str(d))
                        n_tr[k] += 1
                    elif kind == "shadow" and not str(k).startswith("BASE"):
                        shd[k].add(str(d))
            for k, st, d in c.execute("SELECT strategy, status, day FROM signals WHERE run_id=1"):
                if until and str(d) > until:
                    continue
                n_sig[k] += 1
                n_skip[k] += st != "submitted"
        finally:
            c.close()
    out = {}
    for k in sorted(set(act) | set(trd)):
        a, sig = len(act[k]), n_sig[k]
        tags = []
        if a >= TRIAGE_DAYS and sig == 0:
            tags.append("zero-signal")
        if sig >= BLOCKED_MIN and n_skip[k] / sig >= BLOCKED_SHARE:
            tags.append("blocked")
        out[k] = {"active_days": a, "traded_days": len(trd[k]), "trades": n_tr[k], "shadow_days": len(shd[k]),
                  "signals": sig, "blocked_pct": None if not sig else round(n_skip[k] / sig * 100, 1),
                  "verdict_ready": bool(a >= MIN_DAYS and n_tr[k] >= MIN_TRADES), "triage": tags}
    return out


def from_branches(remote: str = "origin", until: str | None = None) -> dict:
    snaps: dict = {}
    with tempfile.TemporaryDirectory() as tmp:
        jpaths = {}
        for acct, b in BRANCHES.items():
            ref = f"{remote}/{b}"
            snaps[acct] = {}
            for f in _git("ls-tree", "--name-only", f"{ref}:setups").split():
                if f.endswith(".json"):
                    try:
                        snaps[acct][f[:-5]] = json.loads(_git("show", f"{ref}:setups/{f}"))
                    except json.JSONDecodeError:
                        pass
            raw = subprocess.run(["git", "-C", str(ROOT), "show", f"{ref}:journal.db"], capture_output=True).stdout
            if raw:
                p = Path(tmp) / f"{acct}.db"
                p.write_bytes(raw)
                jpaths[acct] = p
        return build(snaps, jpaths, until)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Arena reps in active days (C3-ROT)")
    ap.add_argument("--remote", default="origin")
    ap.add_argument("--until")
    ap.add_argument("--out", default=str(OUT))
    a = ap.parse_args(argv)
    reps = from_branches(a.remote, a.until)
    doc = {"note": "C3-ROT rep counts (owner 2026-11-18): live active days, traded days, live trades, shadow days "
                   "(separate column, never in the live record), triage tags. Educational only - not financial advice.",
           "until": a.until, "setups": reps}
    Path(a.out).write_text(json.dumps(doc, indent=1) + "\n")
    ready = sum(v["verdict_ready"] for v in reps.values())
    tri = {k: v["triage"] for k, v in reps.items() if v["triage"]}
    print(f"{len(reps)} setups; {ready} verdict-ready (>= {MIN_DAYS} active days and >= {MIN_TRADES} trades); "
          f"{len(tri)} triage-tagged -> {a.out}")


if __name__ == "__main__":
    main()
