"""OPS-POLL 2026-10-22: decision bars no poll evaluated, per account, from the live poll-input logs.

    python research/ops/pollspeed1022_missed.py <dir with <branch>/2026-10-22/*.jsonl.gz> 2026-10-22

A lab setup evaluates a symbol only when its bar count is a multiple of 5 (LabStrategy.eligible) and the runner acts
only on the latest bar, so a decision bar (count c, c % 5 == 0) is skipped when no poll saw the symbol at exactly c bars.
Per poll the log gives each symbol's count: exp minus k for the symbols listed under miss[k], exp for every other
symbol with bars. Decision bars counted: c in 20..330 (bar closes 09:50..15:00 for a symbol trading every minute = the
lab window). Educational only - not financial advice."""
from __future__ import annotations

import json
import sys
from collections import defaultdict

from mcf.execution.runner import read_poll_log

BRANCHES = {"primary": "mcf-data", "testing": "mcf-data-testing", "testing2": "mcf-data-testing2",
            "gen": "mcf-data-gen", "graveyard": "mcf-data-graveyard"}
LO, HI = 20, 330


def missed(recs: list[dict]) -> dict:
    named: set[str] = set()
    for r in recs:
        for syms in r["miss"].values():
            named.update(syms)
    seen: dict[str, list[int]] = defaultdict(list)
    full_seen: list[int] = []                        # counts of the symbols holding exp bars at every poll
    for r in recs:
        exp = r["exp"]
        lst = {s: exp - int(k) for k, syms in r["miss"].items() for s in syms}
        for s in named:
            seen[s].append(lst.get(s, exp))
        full_seen.append(exp)

    def gaps(counts):
        cs = sorted(set(counts))
        out = []
        for a, b in zip(cs, cs[1:]):
            out += [c for c in range(a + 1, b) if c % 5 == 0 and LO <= c <= HI]
        return out

    got = sorted(r["got"] for r in recs)[len(recs) // 2]
    n_full = max(0, got - len(named))
    fm = gaps(full_seen)
    named_missed = sum(len(gaps(v)) for v in seen.values())
    decision_bars_full = len([c for c in range(LO, HI + 1) if c % 5 == 0])
    return {"polls": len(recs), "symbols_with_bars": got, "full_symbols": n_full,
            "decision_bars_per_full_symbol": decision_bars_full, "full_symbol_bars_missed": len(fm),
            "missed_bar_counts": fm, "symbol_decisions_missed": len(fm) * n_full + named_missed,
            "symbol_decisions_total_approx": decision_bars_full * got}


if __name__ == "__main__":
    base, day = sys.argv[1], sys.argv[2]
    res = {}
    for acct, br in BRANCHES.items():
        recs = read_poll_log(f"{base}/{br}", day)
        if recs:
            res[acct] = missed(recs)
            m = res[acct]
            print(f"{acct:10s} polls {m['polls']:4d}  decision bars missed (full symbols) "
                  f"{m['full_symbol_bars_missed']}/{m['decision_bars_per_full_symbol']}  symbol-decisions missed "
                  f"{m['symbol_decisions_missed']:,} of ~{m['symbol_decisions_total_approx']:,}")
    print(json.dumps({k: {kk: vv for kk, vv in v.items() if kk != "missed_bar_counts"} | {
        "missed_times": [f"{9 + (30 + c) // 60}:{(30 + c) % 60:02d}" for c in v["missed_bar_counts"]]}
        for k, v in res.items()}))
