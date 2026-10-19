"""Setup Generator CLI (owner 2026-10-19). Educational only - not financial advice.

    python -m mcf.research.generator run --date YYYY-MM-DD --n 10 [--apply] [--specs 3000] [--seed S] [--workers 4]

Without --apply: a dry-run report (research/generator/runs/<date>.json is NOT written; summary printed).
With --apply: writes research/generator/modules/GEN-YYMMDD-NN-<slug>.py, appends the setups to config/account_gen.yaml
(setup_order rebuilt), config/setup_names.yaml + docs/live/setup_names.json, a research/ledger.jsonl line, the run
report research/generator/runs/<date>.json and every generated spec's key to research/generator/registry.jsonl.
Runs only outside market hours is NOT required for the gen account (owner: no freeze for this exploration account is
set; the setup-freeze PR check still applies to PRs).
"""
from __future__ import annotations

import argparse
import json
import sys
import time

from .apply import run


def main(argv=None):
    ap = argparse.ArgumentParser(prog="python -m mcf.research.generator")
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--date", required=True)
    r.add_argument("--n", type=int, default=10)
    r.add_argument("--apply", action="store_true")
    r.add_argument("--specs", type=int, default=3000, help="random specs to screen")
    r.add_argument("--seed", type=int, default=None, help="default: the date as YYYYMMDD")
    r.add_argument("--workers", type=int, default=3, help="processes for the history build (I/O bound)")
    r.add_argument("--screen-workers", type=int, default=4)
    a = ap.parse_args(argv)
    t0 = time.time()
    rep = run(a.date, n=a.n, apply=a.apply, n_specs=a.specs, seed=a.seed, workers=a.workers,
              screen_workers=a.screen_workers)
    print(json.dumps({k: rep[k] for k in ("date", "n_tried", "n_scored", "n_tier1", "applied")}, indent=1))
    for p in rep["picks"]:
        tr, va = p["screen"]["train"], p["screen"]["valid"]
        print(f"{p['name']}: train {tr['n']} trades {tr['exp_r']}R t {tr['t']} | valid {va['n']} {va['exp_r']}R t {va['t']}"
              f" | {p['screen']['per_day']}/day | score {p['screen']['score']}")
    print(f"runtime {time.time() - t0:.0f}s. Educational only - not financial advice.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
