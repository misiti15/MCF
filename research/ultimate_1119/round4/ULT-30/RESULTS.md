Educational only — not financial advice

# ULT-30 EARN-DAY2 — day-after-earnings continuation (round 4) — **FAIL**

Research only: no setup, exit, config or account change. Nothing committed. **PARTLY CHECK-INFORMED** (PLAN sec. 0.6).
Any deployment would also **need an owner exception to the 4-day earnings blackout** (sec. 0.8). That question does not
come up, because the candidate fails.

## Verdict
- **Fit pick 30b (|REACT| >= 4%, both sides, TX-45)**: fit **-0.003R** (n 482, 2.84/session, t -0.11).
  - Only 30a and 30b reach 2/session on fit, and both are <= 0.
  - The pick can never reach TIER A, because its fit avg R is not > 0.
- **CHECK, scored once:** **-0.034R**.
  - 1,087 trades, 3.94/session.
  - Without the best day: -0.040.
  - Total -36.9R (-0.134R/session).
  - Day-clustered t **-2.14** (the bar is 3.716).
- **Tier: FAIL.** TIER B would need fit > 0.
  - Of the 8 grid configs, 6 are negative on check.
  - The two positive ones are 30c (+0.005, t 0.12) and 30g (+0.013, t 0.25).
  - The best fit cell, 30h (T8 long-only TX-45: fit +0.096, 0.85/session, t 1.89), falls to **-0.043** on check.
- **The day-2 trigger does worse than random bars on the same names, sessions and sides**, in both halves.
  - Signal minus random: **-0.040 (fit)** and **-0.085 (check)**.
  - Random bars on these RD+1 names earn +0.034 (fit, t 1.77) and **+0.051 (check, t 3.28)**. That is a diagnostic,
    not a candidate (see "Leads").
- **News adds nothing here.**
  - The RD+1 rule (-0.034) is worse than its non-earnings twin (-0.021).
  - The twin is the same rule on names that had a >= 4% move vs SPY the previous session with no report nearby.

## Configurations tried
- This candidate: 8 grid + 1 bias diagnostic = **9**, as PLAN sec. 4.
- Cumulative N for the job stays **996** (round 4's 115 already includes these 9), so the t bar is 3.716.
- The random-entry control, the non-earnings twin and the surcharge sensitivity are reported but not counted.

## What was built
### Module
`research/ultimate_1119/modules/ULT-30.py` is live-ready and uses the round 1-4 interface:
- LabStrategy `type: lab`, two entries in one file ("-S" = short), `context: [spy_fo]`, GEOM "S" for TX-45 or t1s1
  for EXIT T.

How the module finds events live:
- The event source is the allow-list `SYMBOLS` (YAML `symbols: module`): today's RD+1 names with |REACT| >= T and the
  sign of the side.
- It is built at import by `day2_events()`, the same function the backtest uses. It reads two files:
  - the earnings calendar (`MCF_EARN_CAL`, earnings_yf columns);
  - a daily-close file (`MCF_DAILY_CLOSES`: symbol, date, close; it must include SPY). Only rows dated strictly
    before today are read.
- A missing file or missing closes gives an empty list, so no trades (fail safe).
- With long-only, the short entry never fires.

**Deploy gap:** the live runner has no daily-close file today.
- The pre-open prior build fetches 30 daily bars per name but does not persist them.
- The 5-minute warm-up (`prior5`, 60 bars) does not reach RD-1.
- The yfinance report hour is also needed (the same gap as ULT-28).

### Smoke test
`round4/ULT-30/test_module.py` holds 4 tests, all passing with both EXIT values. They cover:
- **Calendar and REACT:**
  - amc gives RD+1 two sessions later, bmo the next session, and dmh is excluded;
  - REACT is computed vs SPY;
  - the T and side filters, long-only, and the fail-safe for each missing file.
- **Point-in-time closes:** changing today's close leaves the allow-list unchanged.
- **Under the live LabStrategy:**
  - long and short both fire;
  - nothing fires on a faded tape, a reversal gap or a non-event name.
- **Features:**
  - a point-in-time truncation test;
  - e_d2 / e_react gating: wrong side, below T and reversal gap.

### Backtest
`round4/ULT-30/bt.py` imports round4/ULT-28/bt.py unchanged: its 1-minute `walk_job` and the ULT-23 stats. New code
covers only the RD+1 event table, the signal superset, the grid and the cost wrapper.
- **Costs:** LR8, the round-3 chassis (one lot per symbol, refire >= 30 min after the exit, max 2 per symbol-session,
  day cap 30, flat 15:50) and next-minute-open fills.
- **Short borrow:** 5 bp of notional on RD+1 (earnings window), 8 bp under $20. Twin shorts pay 1.2 / 3 bp.
  Shorts are ETB only.
- **Surcharge:** the PLAN's x1.5 first-hour surcharge is scoped to RD bars, so it is not in the main figure. A
  sensitivity applies it to RD+1 bars before 10:30. Check pick: -0.0367 with it, vs -0.0339 without.
- **Event volume** (point-in-time counts, no outcomes):
  - RD+1 names per session: ~15-29 in season, ~3-5 off season.
  - With ADV >= $30M and |REACT| >= 4%: ~7-15 in season.
  - Fit holds 2,383 RD+1 events: 1,247 with |REACT| >= 4%, 613 with >= 8%.

### Locked block
- The block is never read.
- Daily bars come from `lib.daily()`, which removes locked rows, and `no_locked` asserts on every load.
- Events whose RD-1, RD or RD+1 falls in the block are dropped, never filled. The first usable fit RD+1 is 2025-03-05.
- Twin REACT is computed only across consecutive sessions, never across the locked gap.
- pyarrow filters and `no_locked` asserts run on every frame and 1-minute load.
- Forbidden columns are dropped and asserted absent.

### Order of steps
1. fitsel.json was frozen at 2026-11-19T09:01:18Z, before any check frame, event row or trade was built. The freeze
   recorded sha256 hashes of bt.py, the module, the ULT-28 bt.py and the earnings file.
2. Check was scored once at 09:03:19Z. The plateau ran after it.
3. After the check score, only the module's pick constants and header line were changed: EXIT "T" became "X" to match
   30b, and the header now reads "fit-frozen 30b, CHECK FAIL". The module's sha256 is now e949087b…e2e9. bt.py
   imports only the functions, never the pick constants.

## FIT grid (170 sessions; selection = max fit total R minus best day among configs >= 2.0/session)
| cfg | rule | /session | avg R | w/o best day | total R | t | A / B | long / short |
|---|---|---|---|---|---|---|---|---|
| 30a | T4 both t1s1 | 2.91 | -0.048 | -0.057 | -23.5 | -1.36 | -0.041 / -0.055 | -0.037 / -0.061 |
| **30b** | T4 both TX-45 | 2.84 | -0.003 | -0.010 | -1.3 | -0.11 | +0.008 / -0.015 | +0.039 / -0.051 |
| 30c | T4 long t1s1 | 1.59 | -0.037 | -0.053 | -9.9 | -0.81 | +0.006 / -0.096 | -0.037 / — |
| 30d | T4 long TX-45 | 1.54 | +0.039 | +0.027 | +10.1 | 1.14 | +0.051 / +0.020 | +0.039 / — |
| 30e | T8 both t1s1 | 1.63 | +0.007 | -0.007 | +1.9 | 0.15 | -0.003 / +0.016 | +0.044 / -0.038 |
| 30f | T8 both TX-45 | 1.57 | +0.045 | +0.034 | +12.0 | 1.38 | +0.063 / +0.028 | +0.096 / -0.014 |
| 30g | T8 long t1s1 | 0.89 | +0.044 | +0.022 | +6.6 | 0.81 | +0.026 / +0.064 | +0.044 / — |
| 30h | T8 long TX-45 | 0.85 | +0.096 | +0.074 | +13.8 | 1.89 | +0.095 / +0.096 | +0.096 / — |

**Volume against the plan:**
- Expected was ~2-4/session for both sides and ~1-2 long-only. Both sides came in at 2.8-2.9 (T4) and 1.6 (T8);
  long-only at 1.5 (T4) and 0.9 (T8).
- Only the T4 both-sides configs reach 2/session, so the pick is 30b. The rule picks the same config by plain total R.

**On fit, the pre-declared long-only / larger-REACT cells look better:**
- Fit shorts lose in every config: -0.014..-0.061.
- But the fit-positive cells sit below the volume bar, and none of them holds on check (see "CHECK plateau").

## Fit pick 30b: FIT vs CHECK
| | FIT | CHECK (once) |
|---|---|---|
| trades (/session) | 482 (2.84) | 1,087 (3.94) |
| sessions traded | 80 of 170 | 150 of 276 |
| win | 0.483 | 0.489 |
| avg R (per 2u, TX-45) | **-0.0026** | **-0.0339** |
| avg R per 0.25-dATR unit | -0.0052 | -0.0678 |
| avg R w/o best day | -0.0097 | -0.0395 |
| best day (share) | 2025-05-07 +3.3R (n/a, total < 0) | 2025-10-29 +5.1R (n/a, total < 0) |
| total R (R/session) | -1.25 (-0.007) | -36.87 (-0.134) |
| worst day (/ trade-session) | -4.61 (-0.77) | -5.32 (-0.74) |
| day-clustered t | -0.11 | **-2.14** (bar 3.716) |
| w/o 2025-04-03..04-09 | -0.0041 (n 481) | n/a (no such dates) |
| sub-halves A / B | +0.008 / -0.015 | — |
| first / second half | +0.011 / -0.018 | -0.021 / -0.045 |
| long / short | +0.039 (n 261) / -0.051 (n 221) | **-0.045** (n 532) / -0.023 (n 555) |
| SPY up / flat / down | +0.001 / +0.033 / -0.045 | -0.039 / -0.045 / -0.016 |
| entry 09:50-10:25 / 10:30-11:25 / 11:30-12:30 | -0.003 / -0.014 / +0.014 | **-0.080** / +0.004 / +0.006 |
| REACT 4-8 / 8-15 / 15+ % | -0.062 / +0.043 / +0.050 | -0.041 / -0.043 / +0.004 |
| s x gap < 0 / 0-2 / 2+ % | +0.054 / -0.040 / +0.026 | -0.027 / -0.023 / -0.090 |
| season / off-season sessions (>= 5 RD+1 names) | -0.013 (n 463) / +0.258 (n 19) | -0.031 (n 1,054) / -0.120 (n 33) |
| median hold; exit mix | 45 min; time 464 / stop 18 | 45 min; time 1,003 / stop 84 |
| surcharge sensitivity (x1.5 before 10:30 on RD+1) | -0.0054 | -0.0367 |
| bias diagnostic (signal-close fill, no borrow) | +0.011 | -0.025 |
| same-name random control (avg R, t; signal minus random) | +0.034, t 1.77; **-0.040** | +0.051, t 3.28; **-0.085** |
| random long / short | +0.066 / -0.004 | +0.073 / +0.029 |
| non-earnings twin (same rule, no report in d-2..d+5) | +0.006 (14.3/session, t 0.35) | -0.021 (23.6/session, t -1.81) |

**Bars:**
- check avg R > 0: no.
- w/o best day > 0: no.
- fit avg R > 0: no.
- >= 2/session: yes.
- BEATS: no. Avg R, w/o best day, total R/session and t all fall short. Worst day / trade-session (-0.74) would pass.

**Sign flip:** the long side is +0.039 on fit and -0.045 on check. The pre-declared "longs good, shorts bad" read from
the daily evidence does not hold intraday from 09:50 on this chassis.

## CHECK plateau (diagnostic only, run after the single check score; never used to re-select)
| cfg | /session | avg R | w/o best day | t | long / short | 1st / 2nd half |
|---|---|---|---|---|---|---|
| 30a | 4.01 | -0.032 | -0.039 | -1.30 | -0.001 / -0.063 | +0.012 / -0.070 |
| **30b (pick)** | 3.94 | -0.034 | -0.040 | -2.14 | -0.045 / -0.023 | -0.021 / -0.045 |
| 30c | 2.00 | +0.005 | -0.010 | 0.12 | +0.005 / — | +0.088 / -0.069 |
| 30d | 1.94 | -0.041 | -0.050 | -1.60 | -0.041 / — | -0.006 / -0.073 |
| 30e | 2.15 | -0.011 | -0.020 | -0.35 | +0.013 / -0.033 | +0.043 / -0.054 |
| 30f | 2.10 | -0.025 | -0.032 | -1.23 | -0.043 / -0.009 | +0.003 / -0.048 |
| 30g | 1.05 | +0.013 | -0.005 | 0.25 | +0.013 / — | +0.117 / -0.068 |
| 30h (fit-best avg) | 1.01 | -0.043 | -0.055 | -1.25 | -0.043 / — | +0.012 / -0.085 |
| twin of 30b | 23.6 | -0.021 | -0.023 | -1.81 | -0.005 / -0.041 | -0.024 / -0.017 |

**There is no plateau:**
- 6 of 8 configs are negative, and none has w/o best day > 0.
- The check second half (2026) is negative in every config: -0.045..-0.085.

## Why it fails (mechanism read)
1. **The first qualifying bar is the open-hour extreme again, as in ULT-28.**
   - "First bar >= 09:50 that holds VWAP and the open in the reaction direction" fires mostly at 09:50-10:25.
   - That block is -0.080 on check and ~0 on fit.
   - Later entries are ~0 to slightly positive: +0.004 and +0.006 on check.
2. **The drift, if any, is not in the trigger.**
   - Random bars on the same RD+1 names, sides and sessions are positive in both halves: +0.034 (t 1.77) and +0.051
     (t 3.28).
   - The confirmation filter selects worse bars than chance, so the tape-confirmation design is the failure, not the
     event.
3. **The bigger-reaction / long-only story from the daily study does not hold intraday from 09:50.**
   - Fit favoured T8 and longs: 30h +0.096.
   - Check reverses it: 30h -0.043, and T4 longs -0.045.

## Leads (optimistic next steps; each would need its own pre-registration and count; CHECK is now read for this idea)
1. **An event-only, timing-neutral entry on earnings names (RD and RD+1), with the reaction, at 10:30-12:30.**
   - This is the same lead ULT-28 found from the other side: its random control was +0.091 fit / +0.044 check, and
     here it is +0.034 / +0.051.
   - Both random controls are conditioned on sessions where the trigger fired. A clean, pre-registered "fixed
     10:30 / 11:00 entry on every with-reaction RD+1 name" test is the natural next step.
   - It would be scored only on fresh data (a forward / replay window), because CHECK has now been read twice for
     this lead.
2. **Never enter on the first confirmation bar of a news name before 10:30.** In both ULT-28 and ULT-30 the
   09:50-10:25 block carries most of the check loss. That points at a general remedy for the earnings family (a
   10:30 earliest entry), not one tailored to a setup.

## Files
All paths are under `research/ultimate_1119/`:
- `modules/ULT-30.py`: the module with the frozen pick 30b; CHECK FAIL is noted in the header.
- `round4/ULT-30/` holds:
  - bt.py and test_module.py;
  - fit_grid.json and fitsel.json;
  - fit_random.json: the random control, uncapped stats and the fit twin;
  - check_once.json;
  - check_plateau.json, including the check twin;
  - check_trades.csv.gz.
- The signal and walked parquet files were in the scratchpad and have been deleted.

## Rule-change context
- Both halves are scored under one fixed rule set: today's LR8 costs, the round-3/4 chassis and the round-4 borrow fix.
  No live rule change falls inside them.
- The live 4-day earnings blackout (owner 2026-10-07) was in force through the whole live record. No live setup
  trades RD+1, so there is no live comparison.

## Known biases (all favour the candidate)
- Today's symbol list (survivorship) flatters longs.
- The ETB flag is today's.
- The earnings table was fetched after the fact (rare date revisions are not modelled).
- The yfinance report hour is assumed to be correct.
- RD+1 carries no first-hour spread surcharge in the main figure. With the surcharge it is slightly worse: -0.037 vs
  -0.034.

Educational only — not financial advice.
