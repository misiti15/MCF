"""Blocked-signal audit, lean Monday run (2026-11-16): sessions 2026-11-13 and 2026-11-16 in all ten intraday accounts.
Lean version of blocked1112_audit.py (no skip pricing / place-in-line): coverage (decision minutes polled, longest gap),
unintended blocks (broker rejects, crosscheck, missed: triggered, no quote, position mismatch), enabled setups with zero
signals 11-12 .. 11-16 (lifetime signal count + last signal day).

    python research/ops/blocked1116_audit.py <scratch>     (same <scratch> layout as blocked1112_audit.py)

Reads only. Writes research/ops/blocked1116_results.json. Educational only - not financial advice."""
from __future__ import annotations

import json
import sqlite3
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from mcf.execution.runner import read_poll_log            # noqa: E402

S = Path(sys.argv[1])
DAYS = ["2026-11-13", "2026-11-16"]
NF_DAYS = ["2026-11-12", "2026-11-13", "2026-11-16"]
ACCTS = {"Primary": "mcf-data", "On Deck": "mcf-data-testing", "Testing A": "mcf-data-testing2",
         "Graveyard": "mcf-data-graveyard", "Generator": "mcf-data-gen", "Testing B": "mcf-data-explore1",
         "Testing C": "mcf-data-livelab", "Testing D": "mcf-data-testingd", "Testing E": "mcf-data-testinge",
         "Testing F": "mcf-data-testingf"}
DEC = set(range(0, 381, 5))


def kind(reason: str, status: str) -> str | None:
    r = reason or ""
    if status == "rejected":
        return "reject:bp" if "insufficient" in r else "reject:other"
    for p, k in (("crosscheck", "crosscheck"), ("missed: triggered", "missed"), ("no quote", "noquote"),
                 ("no two-sided", "noquote"), ("position mismatch", "mismatch")):
        if r.startswith(p):
            return k
    return None


res: dict = {"days": DAYS, "coverage": {}, "unintended": {}, "never_fired": {}}
for acct, br in ACCTS.items():
    cov = {}
    for d in DAYS:
        recs = read_poll_log(str(S / "polls" / br), d)
        if not recs:
            cov[d] = None
            continue
        t = pd.to_datetime([f"{d} {r['t']}" for r in recs])
        g = np.diff(t.values).astype("timedelta64[s]").astype(float) / 60
        i = int(g.argmax()) if len(g) else 0
        miss = sorted(DEC - {r["exp"] for r in recs})
        cov[d] = dict(polls=len(recs), first=recs[0]["t"], last=recs[-1]["t"],
                      max_gap_min=round(float(g.max()), 1) if len(g) else None, max_gap_at=recs[i]["t"],
                      decision_polled=len(DEC) - len(miss), decision_missed=[f"{9 + (30 + m) // 60:02d}:{(30 + m) % 60:02d}" for m in miss],
                      coverage_pct=round(100 * (len(DEC) - len(miss)) / len(DEC), 1))
    res["coverage"][acct] = cov
    c = sqlite3.connect(S / "j" / br / "journal.db")
    sig = pd.read_sql("select day, strategy, status, reason from signals where run_id=1 and day >= '2026-11-12'", c)
    sig["k"] = [kind(r, s) for r, s in zip(sig.reason, sig.status)]
    u = sig[sig.k.notna() & sig.day.isin(DAYS)]
    res["unintended"][acct] = {d: u[u.day == d].k.value_counts().to_dict() for d in DAYS}
    fired = sig[sig.day.isin(NF_DAYS)].groupby("strategy").size().to_dict()
    life = pd.read_sql("select strategy, count(*) n, max(day) last from signals where run_id=1 group by strategy", c).set_index("strategy")
    enabled = {}
    for d in NF_DAYS:
        try:
            fz = json.loads(subprocess.run(["git", "-C", str(ROOT), "show", f"origin/{br}:setups/{d}.json"],
                                           capture_output=True, text=True, check=True).stdout)
        except Exception:
            continue
        for n, s in fz.get("strategies", {}).items():
            if isinstance(s, dict) and s.get("enabled", True) is not False:
                enabled.setdefault(n, []).append(d)
    nf = {n: dict(days=len(v), life=int(life.n.get(n, 0)), last=life["last"].get(n)) for n, v in enabled.items()
          if fired.get(n, 0) == 0 and "2026-11-16" in v}
    res["never_fired"][acct] = dict(enabled=sum(1 for v in enabled.values() if "2026-11-16" in v), never=nf)
    print(acct, {d: v and {k: v[k] for k in ("polls", "first", "max_gap_min", "max_gap_at", "decision_polled", "decision_missed", "coverage_pct")} for d, v in cov.items()})
    print("   unintended", res["unintended"][acct])
    print(f"   enabled {res['never_fired'][acct]['enabled']}, zero signals since 11-12: {len(nf)}")
    for n, e in nf.items():
        print("     NF", n, e)
(ROOT / "research/ops/blocked1116_results.json").write_text(json.dumps(res, indent=1, default=str))
print("Educational only - not financial advice.")
