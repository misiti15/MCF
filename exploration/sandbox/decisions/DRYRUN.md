# Dry run of the prepared decision drafts (2026-11-28, overnight)

Educational only — not financial advice.

**What this is.** Each prepared draft in this folder was applied to a throwaway, detached copy of
`claude/intraday-trading-system-witis4` at commit `f5a2626587` (the branch tip on 2026-11-28 ~01:00 ET). The full test
suite (`pytest -q`) was run on each copy. The copies were never committed or pushed, and were deleted afterwards. The owner's
checkout, `config/`, the paper accounts and the scheduled jobs were not touched. Nothing here is an approval: every draft
still waits for the owner's answer.

Unchanged branch (baseline): **1076 passed, 1 skipped** (10.5 min).

## Results

| Draft | Applies as written? | Tests failing with the draft as written | Fix made to the draft | Full `pytest -q` after the fix |
|---|---|---|---|---|
| LATCH-OPEN (monday) | **No.** `config.diff` uses `@@ risk:` section headers, not real hunks: `git apply` refuses it. The config line itself matches exactly once | 12 in `tests/test_friday_switches.py`: `test_every_switch_defaults_off_in_every_account` x 10 accounts (asserts the switch is off), `test_default_off_runner_noop` and `test_flags_off_full_poll_matches_pre_change_golden` (both read the repo config; the golden test's "hook ran with every switch off" guard fires) | Test edit (shared "base" edit): the defaults test becomes "off unless approved" (`APPROVED_ON` set, one line per approved switch); the two no-op tests pin the switches off themselves (`_switches_off`), because they test the flags-off code path, not the repo config. Ledger: `date` and `approved_by` placeholders made fillable (`<DATE>`, `<WHERE>`) | **1076 passed** |
| LATCH-OPEN variant -3R | config line matches | +3 more in `test_friday_switches.py` (latch tests expect the 2R default threshold from the repo config) | `_rm()` pins `latch_open_r: None` unless a test sets it; ledger patch gains `risk.latch_open_r [null, 3]` | passed (in the all-five run below) |
| L3-OUT (out) | **No** (same `@@` format). All four config lines match exactly once. `python -m mcf.report.assignments` runs clean: L3 primary -> testing, `first_session` 2026-11-30, `last_old_session` 2026-11-27 | 2: `tests/test_c3_epoch_rot_score.py::test_ns5_left_primary_and_runs_in_on_deck_only` (counts 4 setups enabled in Primary; now 3) and `tests/test_remedyq_1120.py::test_parents_unchanged_in_primary` (requires the Remedy-Q parent L3 to be enabled in Primary) | Two test edits (count 4 -> 3 plus `L3 not in on`; the Remedy-Q parent check accepts L3 enabled On Deck, window still [950, 1500]). Ledger: added the protected-list fields the gate requires (`protected_ids` PROT-06/07/08/09/30, `guard_evidence` research/primshorts_1126/REPORT.md, `owner_approval`); `<EFFECTIVE: ...>` placeholder fixed; comment figure -0.204 -> -0.209 R/lot (the ledger's number) | 1075 passed + the 1 fixed test passes (re-run); full pass in the combo and all-five runs |
| B8-SHADOW | **No** (same `@@` format; also its context line for `betas_path` had a different comment from the branch) | the same 12 as LATCH-OPEN | shared base test edit + `APPROVED_ON.add("netbeta_shadow")`; new `ledger.jsonl` (was only a comment) | **1076 passed** |
| ARENA-LATCH-F | **No** (same format); line matches | 1: `tests/test_new_accounts_1111.py::test_overlay_loads_with_its_own_setups[testingf]` (every Testing D-F account must have no per-setup stop) | `ARENA_LATCH = {"testingf": 2.0}` exception in that test; new `ledger.jsonl` with `protected_ids` PROT-21 (its guard says "No latch in Testing", so the owner's approval must be explicit) | **1076 passed** |
| HS-SCALE (shock-only) | **No** (same format); 3 lines match | the same 12 as LATCH-OPEN | shared base test edit + `APPROVED_ON.add("shock_v")`; new `ledger.jsonl` | 1075 passed, 1 failed: `test_poll_log.py::test_overhead_and_size_on_a_live_sized_universe` (CPU-time limit 0.25 s, got 0.27 s while 3 suites ran at once). Passes twice when re-run alone: a load flake, not the draft |
| TAGS2 | not applicable: `rules_draft.json` is a journal-only scoring spec, no code or config. It parses (7 rules, configs = 7) | — | — | — |
| **Monday combo** (LATCH-OPEN + L3-OUT + B8-SHADOW, effective 11-30) | yes with `apply_draft.py`; assignments regenerated | the union of the above | the fixes above compose (one base edit, two `APPROVED_ON` lines) | 1075 passed, 1 failed: the same `test_poll_log` load flake (0.29 s); passes when re-run alone |
| All five, Friday option (12-07), LATCH-OPEN -3R | yes | — | — | **1076 passed** |

## What changed in the drafts

- **`apply_draft.py` (new)** is now the way to apply any draft. Each edit is an exact text replacement that must match exactly
  once, so a config that has moved on since tonight fails loudly instead of half-applying. It also appends the ledger line
  (placeholders filled) and makes the test edits listed above. The old `config.diff` files are kept as the readable view
  and now say so on line 2.
- **Ledger drafts:** placeholders are now `<DATE>` (the owner's reply), `<EFFECTIVE>` (first session: 2026-11-30 for
  `--when monday`, 2026-12-07 for `--when friday`) and `<WHERE>`. New files: `B8-SHADOW/ledger.jsonl`,
  `ARENA-LATCH-F/ledger.jsonl`, `HS-SCALE/ledger.jsonl`. `L3-OUT/ledger_out.jsonl` and `ledger_probation.jsonl` carry
  the protected-list fields (without them `tests/test_protected.py` would fail).
- **`*/dryrun_monday.patch` and `dryrun_combo_monday.patch`**: the exact diffs the dry run produced (against `f5a2626587`,
  date 2026-11-29, `chat`). For reading and review only: their ledger hunks go stale as soon as a new ledger line lands, so
  apply with the script.

## Exact apply commands (on a branch cut from claude/intraday-trading-system-witis4, outside 09:30-16:00 ET)

```bash
D=exploration/sandbox/decisions        # in the explore/2026-11-27 checkout
R=/path/to/checkout                    # the working branch
# Monday combo (owner said LATCH-OPEN monday + L3-OUT out + B8 shadow), effective 2026-11-30:
python $D/apply_draft.py --repo $R --code COMBO --when monday --date <reply date> --where <chat|inbox>
cd $R && python -m mcf.report.assignments          # same commit (L3-OUT is a move)
python -m mcf.research.ledger list | tail -3       # the new entries parse
pytest -q                                          # expect 1076 passed (test_poll_log may flake under load: re-run it alone)
# One draft at a time instead: --code LATCH-OPEN [--variant 3R] | L3-OUT | B8-SHADOW | ARENA-LATCH-F | HS-SCALE
# Friday-epoch timing: --when friday (effective 2026-12-07)
```

Then, as each draft's notes say: `python -m mcf.research.ledger check` (not run here: it needs the bar cache and runs a
full joint backtest per ledger entry), the decisions.json card set to answered, and the first-day status checks.

## Things the owner or the applying session should know

- **Not tested here:** `python -m mcf.research.ledger check` and any live behaviour. This run only shows the drafts apply
  and the suite passes.
- **HS-SCALE floors:** with the scaled halt off, SHOCK-V uses the floors alone (X = 0), so the bar is a 16R fall in
  2 minutes or 24R in 10. Those floors were scored with 4 Primary setups; with L3 out (3 setups) the matching levels
  would be 12 / 18, which were not scored.
- **L3-OUT and its Remedy-Q copy:** `L3-gap-slope-fromopen-FD-RQa-1230` keeps running in Testing F. After the move the
  parent runs On Deck, so the parent-vs-copy comparison becomes arena vs arena. No conflict (separate accounts).
- **ARENA-LATCH-F:** none of Testing F's 22 setups has its own `max_setup_daily_loss_r`, so the 2R stop reaches all of them.
  It is raw R (Testing F is not in `loss_stops_cost_r_accounts`).
- **Epoch tag:** the 11-30 ETF-STOP50/AV50 entry carries `"epoch": 3`. If LATCH-OPEN / L3-OUT go in on Monday, the applying
  session may add the same tag to their ledger lines (optional; no test needs it).

## Counts and rule context

- Strategy configurations tried: **0** (this is a mechanics check, not research; no performance figures are produced).
- Test runs: 1 baseline + 7 full `pytest -q` runs (LATCH-OPEN, L3-OUT, B8-SHADOW, ARENA-LATCH-F, HS-SCALE, Monday combo,
  all five Friday/-3R) + targeted re-runs.
- Rule changes in force around the dates: the branch already holds the 11-30 ETF-STOP50/AV50 change and the 11-27 Friday
  review moves (effective 11-30); earlier: 11-12 LR8/LR3, 11-19 Epoch 1, 11-20 stop rounding, 11-23 ST7 out +
  BRAKE-BURST, 11-27 ROT-B3. The Monday combo would start on the same session as AV50, so a later read of 11-30 onwards
  must keep the two apart.
- Locked holdout 2024-11-01..2025-02-28: not read.
