# U11 ONE ENGINE — plan (written 2026-11-18, before the census was summarised)

*Educational only — not financial advice. Research only: no code, config, runtime, setup or exit change; no merge,
no PR (market hours). USAGE PLAN item 11, owner-approved 2026-11-18. Source names as in docs/GLOSSARY.md.*

## Question

MCF runs several engines that simulate trades (the old backtester, the lab-frame 2-year pipeline / Generator screen,
the session replay through the live runner, the calibrated replay, and per-study bespoke sims). Which engine is used by
whom, where do they disagree (measured, from the scorecards already on the branch), and what must hold before the old
engine(s) are retired in favour of ONE engine of record (the live runner code via `mcf/replay`)? Output: a concrete
retirement plan with steps, tests and a decision code. **No code changes now.**

## Method (fixed now)

1. **Inventory by reading code** on origin/claude/charming-mccarthy-i3rhhr: module docstrings, imports, CLI entry
   points, `.github/workflows/*`, tests. One row per engine: entry point, signal path, fill model, cost model, R
   definition, universe, book/limits, speed, tests.
2. **Who uses which — census** (`code/census.py`): every `.py` under `mcf/`, `research/`, `scripts/` classified by
   regex markers (Backtester class; `simulate`/`Costs` primitive; lab frames — `history2y` / `setup_lab` / `load_month` /
   arena / generator; live-code replay — `mcf.replay.harness|livecal|fast|broker`, `run_session`, `mcf.report.team`;
   bespoke — own `sim*/engine*/replay*.py` or own `simulate`/`first_touch` walker with none of the above). First-add date
   from `git log --diff-filter=A`. Counted per file and per study directory, split <= 10-31 / 11-01..11-10 / 11-11..11-18.
   It is a heuristic (regex), stated as such.
3. **Where they disagree — no new scoring.** Only numbers already measured and committed: research/replay_cal
   (held-out scorecard, scored once), research/replay/VALIDATION.md, research/src_value (SRCV1), research/fwdrep,
   research/history2y/RESCORE.md + parity.json, Workbench RESULTS files. Each number is quoted with its source, window
   and the rule changes inside it.
4. **Preconditions** for retirement checked as of today: (a) session replay matches live >= 98% / <= 2% extra /
   |bias| <= 0.01R not optimistic on held-out overlap days (research/replay_cal/TARGETS.md); (b) the 2-year live-code
   replay (research/replay2y) is running with its overlap check done.

## Not done (by rule)

No setup is scored, tuned or compared, so no locked holdout is touched (the locked block 2024-11-01..2025-02-28 is
never read; no bars are read at all). Configurations tried: **0** setup configurations; 1 census pass. No replay is
run (market hours; the replay_cal/replay2y numbers are cited, not recomputed).

## Output

research/usage/u11_engine/: PLAN.md (this), NOTES.md (method details, caveats), RESULTS.md (inventory, users,
disagreements, precondition status, retirement plan, decision code), u11_engines.csv, u11_consumers.csv,
u11_parity.csv, u11_gates.csv, u11_census.csv, code/census.py.
