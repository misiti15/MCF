# U11 ONE ENGINE — notes

*Educational only — not financial advice. Research only; no code / config / runtime change.*

## How the inventory was built

- Read on origin/claude/charming-mccarthy-i3rhhr at 3aea3f4dc (2026-11-18): module docstrings and imports of
  mcf/backtest, mcf/replay, mcf/research (setup_lab, backlog_lab, generator, arena, ledger, workbench), mcf/report
  (team, exposure_lab, sim_board, engine = the Workbench blueprint drawing, not a simulator), mcf/execution/runner.py,
  .github/workflows (trade, eod, discover, store-bars), tests/test_engine.py, test_replay.py, test_replay_livecal.py,
  test_team.py; docs/GLOSSARY.md, docs/RESEARCH_RULES.md rule 12 and rule 21; research/replay_cal, research/replay,
  research/replay2y, research/src_value, research/fwdrep, research/history2y, research/workbench, research/l3_bespoke_1117,
  research/usage/u4..u8.
- `git grep` of every import of `mcf.backtest` (u11_consumers.csv): the live runner itself imports Costs,
  in_play_filter, is_extended, rank_contexts, simulate, universe_ok from mcf/backtest/engine.py (runner.py:29) and
  uses `simulate()` for the what-if of every signal it did not take (runner.py:2069). risk.py uses lot_shares /
  slot_notional, data/universe.py and replay/harness.py / report/team.py use pinned_symbols. So "retire the old
  engine" can only mean the `Backtester` class (and its callers) — the module also holds live helpers that must be
  moved, not deleted.
- `research/ledger_check.json` (the output of the mandated `python -m mcf.research.ledger check`) is not in the git
  history of the branch, and no workflow runs the check: the one procedure CLAUDE.md requires after every approved
  change runs on the legacy engine and leaves no committed trace. Worth knowing before it is ported.

## Census (code/census.py -> u11_census.csv)

Heuristic regex classification of 726 `.py` files under mcf/, research/, scripts/ (a file can carry several labels;
"BESPOKE" = own sim/engine/replay file or own walker with none of the shared engines; `mcf/report/sim_board.py` is a
false positive there — it only reads results). Study directory = research/<area>/<study>.

| engine label | study dirs (all time) | added <= 10-31 | 11-01..11-10 | 11-11..11-18 |
|---|---|---|---|---|
| Lab frames (E2: history2y / setup_lab / arena / generator) | 150 research + 4 mcf | 87 | 40 | 29 |
| Bespoke sims (E4) | 57 research + 3 mcf | 20 | 12 | **28** |
| Live-code replay (E3: harness / livecal / team) | 13 research + 3 mcf | 5 | 5 | 8 |
| Backtester class (E1) | 10 research + 4 mcf | 13 | 0 | 1 (workbench/orb20_a) |
| simulate() primitive (E1p) | 14 research + 1 mcf (live runner) | 14 | 0 | 1 (orb20_a) |

(Per-period counts are by the first-add date of the files; a study counted in two periods had files added in both.)

Reading: the old Backtester is already nearly dead in research (one new user since 11-01). The growth is in **bespoke
sims**: 28 study directories with their own simulator in the last 6 sessions, 20 of them Workbench setups
(`research/workbench/<setup>/code/sim*.py`) plus l3_bespoke_1117, lr6, sizing_1115 and today's U4/U5/U6. Each
re-implements the setup's conditions, the fill rule, the cost model and the book. That — not the Backtester — is the
real "many engines" problem today.

## Naming clash to fix

In Workbench RESULTS files, "replay" means *the Workbench engine run on the live sessions* (bespoke sim on lab frames),
e.g. research/l3_bespoke_1117/RESULTS.md: "Replay = the Workbench engine on the live sessions". docs/GLOSSARY.md
"Session replay" means *the live runner code* (mcf/replay). The same word now names two different engines whose
numbers differ for the same setup (L3-gap-slope-fromopen-FD, Primary: live runner replay avg R +0.099 on 11-02..11-16,
44% match; Workbench "replay" parent +0.136R over 25 sessions to 11-17, after an earlier Workbench book gave +0.059R).
Until S6, Workbench numbers should be labelled "Workbench sim (live sessions)".

## Caveats

- No disagreement number here is new; each is quoted from the committed scorecard named next to it, with its window.
  The cross-engine numbers come from different windows and setups, so they are not one comparison table — the plan
  makes one (S1 baseline) rather than mixing them.
- The census is regex-based (stated); it under-counts studies that call engines indirectly through shell commands.
- Rule / config changes inside the cited windows (research/ledger.jsonl): replay_cal held-out 11-02..11-16 spans the
  11-03 Testing 2 top-500 pool (UNI1), 11-04 low-rep homes, 11-10 TEAM-6 Primary, the 11-12 batch (LR3 Primary loss
  stops in cost R, LR8 live cost model, account halt 300, Testing A full universe, testing generic cap 30, On Deck
  split-tape gate off) and 11-16 TSZ1 testing sizing / kill-flat-open / shadow mode; the replay runs the setups and
  limits as traded each session, so these sit on both sides. Recorded live quotes start 2026-11-18
  (2026-11-17-record-live-quotes) — the first change that can close the largest replay gap. SRCV1 (history weight
  0.175 -> 0) effective 11-18. VALIDATION.md (10-07..10-21) predates the 10-19 twin block on some sessions.
- Locked block 2024-11-01..2025-02-28: never read (no bars read at all).
