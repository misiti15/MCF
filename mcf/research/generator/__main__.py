"""Setup Generator CLI (owner 2026-10-19). Educational only - not financial advice.

    python -m mcf.research.generator run --date YYYY-MM-DD --n 10 [--apply] [--specs 3000] [--seed S] [--workers 4]
                                         [--no-seeds] [--discovery PATH]
    python -m mcf.research.generator summary      # rebuild docs/live/generator_lab.json (Generator Lab card)
    python -m mcf.research.generator expected     # GX5 backfill: expected live trades/day per GEN setup

Without --apply: a dry-run report (research/generator/runs/<date>.json is NOT written; summary printed).
With --apply: writes research/generator/modules/GEN-YYMMDD-NN-<slug>.py, appends the setups to config/account_gen.yaml
(setup_order rebuilt), config/setup_names.yaml + docs/live/setup_names.json, a research/ledger.jsonl line, the run
report research/generator/runs/<date>.json and every generated spec's key to research/generator/registry.jsonl.
Setup lab seeds (owner 2026-10-19): every run also translates the replicated rules of the latest weekly Setup lab scan
(origin/mcf-data:discovery/latest.json, or --discovery PATH; missing -> no seeds) into a few generator specs
(mcf/research/generator/seeds.py) and screens them with the random specs - same screen, ranking and pick rules,
counted in n_tried. A seeded pick carries screen.seed = {source, layers, ...} in the run report (Generator Lab card:
seeded_from_lab). --no-seeds screens random specs only.
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
    r.add_argument("--no-seeds", action="store_true", help="do not add the weekly Setup lab rules (seeds.py)")
    r.add_argument("--discovery", default=None, help="discovery latest.json path (default: origin/mcf-data via git)")
    sub.add_parser("summary", help="rebuild docs/live/generator_lab.json (Generator Lab card)")
    x = sub.add_parser("expected", help="GX5 backfill: expected live trades/day of every GEN setup "
                                        "(research/generator/expected_live.json), then rebuild the summary")
    x.add_argument("--workers", type=int, default=3)
    a = ap.parse_args(argv)
    if a.cmd == "expected":
        from .expect import backfill
        from .summary import write
        rep = backfill(workers=a.workers)
        write()
        for k, v in rep["setups"].items():
            print(f"{k}: screen {v['per_day']}/day, median day (last 60) {v['per_day_median60']}, "
                  f"expected live {v['expected_live_per_day']}/day")
        print("Educational only - not financial advice.")
        return 0
    if a.cmd == "summary":
        from .summary import write
        d = write()
        print(json.dumps({k: d[k] for k in ("generated", "setups_generated", "live_in_gen", "specs_screened")}))
        return 0
    t0 = time.time()
    rep = run(a.date, n=a.n, apply=a.apply, n_specs=a.specs, seed=a.seed, workers=a.workers,
              screen_workers=a.screen_workers, seeds=not a.no_seeds, discovery=a.discovery)
    print(json.dumps({k: rep[k] for k in ("date", "n_tried", "n_scored", "n_tier1", "applied")}, indent=1))
    if rep.get("seeds"):
        sd = rep["seeds"]
        print(f"seeds ({sd['source']}): {sd['replicated']} replicated rules, {sd['mapped']} mapped, "
              f"{len(sd['skipped'])} skipped, {sd['seeds']} seed specs screened ({sd.get('ranked')} rankable, "
              f"{sd.get('tier1')} tier 1), {sd.get('picked')} picked")
    for p in rep["picks"]:
        tr, va = p["screen"]["train"], p["screen"]["valid"]
        tag = " [seed]" if p["screen"].get("seed") else ""
        print(f"{p['name']}{tag}: train {tr['n']} trades {tr['exp_r']}R t {tr['t']} | valid {va['n']} {va['exp_r']}R t {va['t']}"
              f" | {p['screen']['per_day']}/day (expected live {p['screen'].get('expected_live_per_day')}/day)"
              f" | score {p['screen']['score']}")
    print(f"runtime {time.time() - t0:.0f}s. Educational only - not financial advice.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
