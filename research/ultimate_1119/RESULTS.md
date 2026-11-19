Educational only — not financial advice

# "Ultimate setup" overnight job (2026-11-18/19): results

The owner asked for setups built from scratch out of everything MCF has learned: high volume, long and short, any
market, high avg R after costs, entries from 09:50, flat by 15:50, holds of about 5-45 min.
Owner, same night: **"I don't want to force weak setups."**

**Result: 0 of 10 candidates passed. Nothing was deployed.** No account, setup, exit or config was changed.

## In plain words
- We built 10 candidate setups from the best clues in the live record, the 2-year history and the Move Hunt work:
  6 long, 4 short, 2 that trade both sides or switch with the market.
- Each one was tuned only on the first part of the 2-year history (the "fit" half, 170 sessions). The best version
  was locked in writing **before** the second part (the "check" half, 276 sessions) was opened, and it was scored there
  once. Costs were always in. The locked block (2024-11-01..2025-02-28) was never read.
- **Every candidate lost money on the check half after costs** (avg R -0.003 to -0.157 per trade). Seven of the ten
  already lost on the fit half. Where the fit half looked good, the gain came almost entirely from one crash-rebound
  day (2025-04-04 or 04-09).
- The volume part worked. Several candidates traded 6-21 times per session. What was missing was an edge that holds
  after costs.
- A second reviewer (a skeptic) checked each result and upheld FAIL on all 10. The flaws they found (no short-borrow
  fee, today's symbol list, fills at the signal bar's close) would all make the numbers **worse**, not better.
- What we keep: several triggers pick better entries than random ones on the same names (+0.02 to +0.26R). The
  starting point (for example, shorting gap-down names at midday) loses so much that the trigger only shrinks the
  loss. These triggers are possible filters for future setups, not setups on their own.
- The benchmark tells the same story. On this same 2-year test only two current setups are positive on the check
  half: ST7-FD (+0.084R) and NM-ETF-late-dip (+0.052R). None of the new candidates came near them.

## Deploy bar (pre-registered in PLAN.md sec. 6)
- **TIER A** (may go to a testing arena): check avg R > 0, check avg R without the best day > 0, fit avg R > 0,
  at least 2.0 trades/session on check, no look-ahead.
- **TIER B** (near miss, next round only, never deployed): fit avg R > 0 and check avg R > -0.02.
- Otherwise FAIL.
- **Benchmark bar** (BENCHMARK.md, does not change the tier): check avg R > +0.0836, avg R without the best day
  > +0.0734, total R/session > 0, and worst day / trade-session >= -2.152.

## Every candidate (fit-selected config; R per unit of risk, LR8 costs in)

| # | Candidate | Side | Chosen config | FIT trades/sess | FIT avg R | FIT avg R w/o best day | FIT best-day share | CHECK trades/sess | CHECK avg R | CHECK avg R w/o best day | CHECK best-day share | CHECK total R | CHECK SPY up / flat / down | vs random (check) | Replay | Tier | Beats benchmark? |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 01 | Gap-down pop fade (Cell A core) | short | 01f 11:00-15:00, RSI5 60-90, 45-min exit | 3.46 | -0.047 | -0.060 | n/a (total < 0) | 6.26 | -0.003 | -0.008 | n/a | -5.6 | -0.076 / -0.010 / +0.038 | +0.066 better | not run | FAIL | No |
| 02 | Tape-flush washout long (S4) | long | 02k SPY 30-min < -0.50%, deep washout, 45-min exit | 2.03 | +0.129 | -0.001 | 101% **1 day** (2025-04-04) | 1.83 | -0.091 | -0.185 | n/a | -46.1 | -0.367 / +0.059 / -0.126 | +0.116 better (same-moment names) | not run | FAIL | No |
| 03 | RSI-collapse dip buy, broadened (ST7 chassis) | long | 03b RSI <= 30, ADV $20M, 45-min exit | 9.52 | -0.019 | -0.028 | n/a | 15.26 | -0.006 | -0.008 | n/a | -26.9 | +0.015 / +0.002 / -0.046 | +0.060 better | not run | FAIL | No |
| 04 | Down-tape pop fade short | short | 04j SPY <= -0.50%, RSI5 80-90, 1R/1R cap 45 | 0.44 | +0.023 | -0.034 | 221% **1 day** (2025-04-10) | 0.41 | -0.078 | -0.129 | n/a | -8.8 | -0.839 / -0.546 / +0.077 | -0.112 worse | not run | FAIL | No |
| 05 | With-the-gap continuation (two-sided) | both | 05h gap >= 3%, 10:15-14:00, 45-min exit | 13.05 | -0.011 | -0.019 | n/a | 20.61 | -0.003 | -0.006 | n/a | -15.3 | -0.003 / -0.001 / -0.006 | +0.007 (none) | not run | FAIL | No |
| 06 | Late morning-turn long | long | 06a 10:50-11:30, reclaim 0.3 ATR, 30-min exit | 11.15 | +0.032 | -0.009 | 127% **1 day** (2025-04-04) | 14.45 | -0.091 | -0.099 | n/a | -362.0 | +0.055 / -0.018 / -0.311 | -0.029 worse | not run | FAIL | No |
| 07 | Afternoon volatile dip buy (NM-ETF chassis, broadened) | long | 07a ATR >= 3%, drop 1.0 ATR, 0.5R/1R cap 45 | 2.54 | -0.042 | -0.058 | n/a | 5.45 | -0.030 | -0.037 | n/a | -44.6 | -0.023 / -0.017 / -0.040 | +0.020 better | not run | FAIL | No |
| 08 | Afternoon overbought roll-over short | short | 08g up >= 2.0 ATR, RSI5 >= 85 turning, 20-min exit | 0.34 | +0.052 | +0.027 | 76% **1 day** (2025-04-09) | 0.45 | -0.053 | -0.062 | n/a | -6.6 | -0.032 / -0.067 / -0.048 | +0.030 better | not run | FAIL | No |
| 09 | Failed VWAP reclaim short on a weak tape | short | 09c SPY <= -0.20%, 10:30-15:00, 1R/1R cap 45 | 1.01 | +0.067 | +0.012 | 85% **1 day** (2025-04-03) | 1.17 | -0.157 | -0.185 | n/a | -50.6 | -0.793 / +0.021 / +0.089 | -0.087 worse | not run | FAIL | No |
| 10 | Regime-switch book (all of the above, routed by SPY state) | both | 10d T = 0.50%, each part's fit pick | 14.8 | +0.004 | -0.005 | 231% **1 day** (2025-04-04) | 20.8 | -0.039 | -0.042 | n/a | -224.4 | -0.027 / -0.011 / -0.091 | -0.045 worse | not run | FAIL | No |

Notes on the table:
- "Best-day share" is n/a when total R is below zero. SPY day types are end-of-day labels (09:30 to 15:59, +-0.30%),
  used only for reporting, never at entry.
- "vs random" = signal avg R minus a random entry on the same symbol-sessions, side and exit (ULT-02 uses the
  same-moment random-names control).
- Check halves (first / second): 01 -0.012 / +0.005; 02 -0.185 / +0.090; 03 -0.008 / -0.005; 04 -0.098 / -0.003;
  05 -0.029 / +0.018; 06 -0.095 / -0.086; 07 -0.018 / -0.040; 08 -0.091 / +0.013; 09 -0.171 / -0.123;
  10 -0.065 / -0.010.
- Worst check day (R): 01 -9.1, 02 -37.7, 03 -16.3, 04 -13.2, 05 -14.4, 06 -57.8, 07 -16.0, 08 -1.7, 09 -27.9,
  10 -28.8. Median holds: 30-45 min (08: 20 min).
- **Plateau check** (all grid configs scored on check after the single check score, never used to re-select): every
  config of 01, 03, 04, 06, 08, 09 and 10 is negative on check. 02 has 11 of 12 negative. In 05 and 07 a few configs
  are slightly positive on check, but they were the worst on fit and each rests on one day. That is a sign flip, not a
  plateau.
- **Replay:** not run for any candidate. Every candidate already fails the 2-year test, so a replay could not change
  a tier. The recorded-quote replay also holds only one session (2026-11-18, about 1 h per run).
- **Volume was too low for 04, 08 and 09** (0.4-1.2/session against the 2.0 floor). The PLAN expected 3-15 per
  session for these. The combined conditions almost never occur together.

## Skeptic review (all 10 upheld as FAIL)
- **Selection was clean everywhere.** Each fitsel.json was frozen, with a timestamp, before any check data was built.
  check_selected / check_once files match the reported numbers (spot re-scores for 01, 02, 03, 04, 09 and 10).
- **Locked block guarded everywhere.** Every bt.py refuses MCF_HIST_ALLOW_LOCKED, excludes the locked months and runs
  no_locked() asserts. Builders of 01 and 02 disclosed one unfiltered read of SPY.parquet to check its format or date
  range; no locked-block value was printed or scored.
- **Remaining biases all favour the candidates**, so the true results are worse: no short-borrow fee (01, 04, 05, 08,
  09, 10), today's symbol list flatters longs (02, 03, 06, 07), fills at the signal bar's close, and target fills
  with zero exit cost (10).
- **Small points:** 05's bt.py was modified one minute after its fitsel freeze (no effect on a FAIL). 10's day cap was
  exceeded once (31 trades on one day). 07 and 08 ran 14:00-15:00, not to 15:15/15:20, because the frames and the live
  engine stop at the 15:00 bar. 03 never fires at 10:15 because the SPY 30-min return is missing at that bar.
- **Post-hoc slices are not evidence:** 01's SPY-down sessions (+0.038), 04's "sessions ending down" (+0.077), 09's
  "+0.015 without two herd days" and the uncapped variants were all sliced after the fact. None may be used to
  promote anything.
- **Module check:** each candidate has a live-interface module under research/ultimate_1119/modules/ whose smoke test
  passes under the live LabStrategy. They are faithful builds for the record, **not for deployment**.

## Configurations tried (whole job)

| Stage | Configs |
|---|---|
| Evidence: live record (evidence_live.md) | 230 |
| Evidence: Move Hunt long (fit half only) | 104 |
| Evidence: Move Hunt short (fit half only) | 240 |
| Evidence: archive synthesis | 0 |
| Benchmark (current best setups, fixed rules) | 1 |
| ULT-01 (8 grid + 2 diagnostics) | 10 |
| ULT-02 (12 grid + 1 diagnostic) | 13 |
| ULT-03 (8 grid + 4 diagnostics) | 12 |
| ULT-04 (12 grid + 2 diagnostics) | 14 |
| ULT-05 (8 grid + 3 diagnostics) | 11 |
| ULT-06 (8 grid + 1 diagnostic) | 9 |
| ULT-07 (8 grid + 3 diagnostics) | 11 |
| ULT-08 (8 grid + 2 diagnostics) | 10 |
| ULT-09 (8 grid + 2 diagnostics) | 10 |
| ULT-10 (4 grid; 3 extra uncapped diagnostics computed, unused) | 4 (+3) |
| **Candidates total** | **104** (PLAN pre-registered 94; the extra 10 are diagnostics) |
| **Whole job** | **679** (682 including ULT-10's 3 unused diagnostics) |

Random-entry controls (one per candidate) are reported, not counted. 10 fit-selected configs were scored on check
once each. 0 passed TIER A, 0 reached TIER B.

## Rule changes in effect inside the windows (CLAUDE.md, owner 2026-11-02)
- **2-year fit and check halves** (2024-10, 2025-03..09 / 2025-10-01..2026-11-04): candidates and benchmark are scored
  with one fixed rule set (today's), so no rule change falls inside these results.
- **Live evidence window 2026-10-06..11-18** (used to choose the candidates, not to score them; research/ledger.jsonl
  has 225 entries effective in this span): 10-12 Testing full-day versions; 10-13/14 per-lot stacking and refire
  (refire option B for L3-fromopen); 10-15/10-20/10-21 promotions and demotions plus the Graveyard account; 10-20 twin
  cap and -2R per-setup loss limit; 10-23 per-setup daily loss latches; 10-28 Primary sizing ~$5k -> ~$4k; 10-29 -2R
  latch + BAR90; 10-30 Testing 1/2 cost filter max_stop_cost_r 0.15; 11-05 ROLL1 (Explore 1 / Live Lab); 11-11 TEAM-6;
  **11-12 LR1/LR3/LR7 + LR8 cost model + Testing D/E/F start** (also the biggest single live session; it is the best
  day in ULT-01's Cell A evidence, 69% share); 11-16 ROT1; 11-17 TSZ1 half-size Testing lots + SPYEXIT engine + 15
  Workbench copies; 11-18 GY-BENCH. Moves: L3-fromopen promoted 10-20, demoted 10-22, re-promoted 10-30; ST7-FD
  promoted 10-26; L3-rsi5hi promoted 10-30, back to Testing 11-11. Every live figure is on the one LR8 basis.
- **Effective 2026-11-19** (after every window): USAGE1 routine cadence, the tweaked-copies policy and the 11-18
  housekeeping bundle. None of them is a setup, exit or sizing change.

## What to try next (backlog ideas, untested; each would be a new pre-registered, counted round)
- Use the triggers that beat random entries (01 gap-down pop, 03 RSI collapse, 08 roll-over) as **filters on a book
  whose base rate is already positive**, not as setups on their own.
- A tape-reversal brake (exit or stop new entries when SPY turns back up). The down-tape shorts (04, 09) lost almost
  all of it on sessions where the morning sell-off reversed.
- 07: broaden NM-ETF WB4's own trigger unchanged and change only the universe. The new RSI5-cross trigger is what
  failed, not the broader universe.
- 05: the with-gap intake gives 13-21 trades/session on both sides. A "trend day so far" layer is the targeted next
  test for its flat-tape failure.

## Files
- Plan and bar: research/ultimate_1119/PLAN.md. Benchmark: research/ultimate_1119/benchmark/BENCHMARK.md, benchmark.json.
- Per candidate: research/ultimate_1119/ULT-*/RESULTS.md, bt.py, score.py, fitsel.json, fit grid, check files, smoke test.
- Modules (record only, not deployed): research/ultimate_1119/modules/ULT-*.py.

Educational only — not financial advice.
