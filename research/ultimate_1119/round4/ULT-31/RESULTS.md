Educational only — not financial advice

# ULT-31 EARN-AWARE RANK — learned ranker with information-state features (round 4) — **FAIL**

Research only: no setup, exit, config or account change. Nothing committed. **PARTLY CHECK-INFORMED** (PLAN sec. 0.6).
The pick trades only earnings-window rows, so any deployment would also **need an owner exception to the 4-day
earnings blackout** (sec. 0.8). That question does not come up, because the candidate fails.

## Verdict
- **Fit pick 31f (EVT universe, RS sign-stable ridge, k 8):** walk-forward OOF fit is **+0.0041R**.
  - 361 trades, 3.44/session, t +0.09.
  - Without the best day it is -0.014. The best day is 430% of the total (**1-day tag**).
  - Of the 8 configs, 4 reach 2/session (31b, 31d, 31f, 31h). 31f is the only one of the four with positive fit R.
    The PLAN rule (fit total R minus best day) and the task rule (fit total R) both pick 31f.
- **CHECK, scored once:** **-0.0425R**.
  - 1,782 trades, 6.46/session.
  - Without the best day: -0.049. Total -75.7R (-0.274R/session).
  - Day-clustered t **-2.61** (the bar is 3.716).
- **Tier: FAIL.** check avg R is not > 0. TIER B needs check > -0.02, and -0.0425 misses it.
- **Signal minus random is negative on check.**
  - The random control takes the same names, sessions and sides, with a random eligible EVT bar.
  - Fit: +0.075 (random -0.071). Check: **-0.023** (random -0.020, t -1.52).
  - So the ranker's fit "edge over random" did not carry over.
- **The grid flips sign between halves.** Fit-best cells lose on check, and fit-worst cells win on check:
  - 31e: fit +0.059, check -0.042.
  - 31g: fit -0.027, check +0.053 (t 1.58, 1.7/session).
  - 31h: fit -0.052, check +0.012.

  This is the ULT-11/19/20/21 failure again, now with earnings features in the model.
- **The earnings features did not make the ranker stable.**
  - Sign-stability selection kept 5 of the 8 earnings features in the final 31f model: e_rd, e_rd1, e_bmo,
    s x sign(surprise) and s x REACT.
  - But the model is still led by side-signed SPY / QQQ state (-0.035 / +0.026, which largely offset each other)
    and by is_long.
  - 98% of the pick's fit trades are long.

## Configurations tried
- This candidate: 8 grid + 1 bias diagnostic = **9**, as PLAN sec. 4.
- Cumulative N stays **996**: round 4's 115 already includes these 9. The t bar is sqrt(2 ln 996) = **3.716**.
- The random-entry control and the check plateau are reported but not counted. Walk-forward folds and LOMO
  sign-stability refits are part of each named config.

## Fit grid (walk-forward OOF, folds 2025-05..09; 105 OOF sessions) and check plateau (diagnostic only, 276 sessions)
| cfg | label | fit trades | fit /sess | fit avg R | fit w/o best day | fit total R | fit t | fit A / B | check /sess | check avg R | check w/o best day | check total R | check t | check long / short avg R |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 31a | ALL-RS-k3 | 198 | 1.89 | -0.019 | -0.029 | -3.8 | -0.60 | -0.051 / -0.002 | 4.08 | -0.035 | -0.039 | -39.9 | -1.91 | -0.036 / -0.030 |
| 31b | ALL-RS-k8 | 578 | 5.51 | -0.016 | -0.022 | -9.0 | -0.93 | -0.002 / -0.022 | 10.95 | -0.024 | -0.027 | -73.6 | -1.82 | -0.024 / -0.026 |
| 31c | ALL-GB-k3 | 136 | 1.30 | -0.045 | -0.063 | -6.1 | -1.39 | -0.079 / -0.028 | 3.07 | -0.017 | -0.023 | -14.4 | -0.86 | -0.012 / -0.023 |
| 31d | ALL-GB-k8 | 540 | 5.14 | -0.058 | -0.065 | -31.4 | -2.85 | -0.067 / -0.054 | 6.49 | -0.022 | -0.027 | -39.4 | -1.50 | -0.013 / -0.031 |
| 31e | EVT-RS-k3 | 116 | 1.10 | +0.059 | +0.005 | +6.8 | +0.68 | +0.130 / +0.028 | 2.55 | -0.042 | -0.046 | -29.5 | -2.09 | -0.040 / -0.066 |
| **31f** | **EVT-RS-k8 (pick)** | 361 | 3.44 | +0.004 | -0.014 | +1.5 | +0.09 | +0.038 / -0.012 | 6.46 | **-0.0425** | -0.049 | -75.7 | **-2.61** | -0.046 / +0.004 |
| 31g | EVT-GB-k3 | 166 | 1.58 | -0.027 | -0.057 | -4.4 | -0.40 | +0.002 / -0.046 | 1.74 | +0.053 | +0.041 | +25.3 | +1.58 | +0.035 / +0.199 |
| 31h | EVT-GB-k8 | 384 | 3.66 | -0.052 | -0.072 | -20.0 | -1.20 | -0.058 / -0.049 | 5.18 | +0.012 | +0.007 | +17.1 | +0.64 | +0.006 / +0.071 |

- Fit A = the 2025-05 part of OOF; fit B = 2025-06..09.
- The ALL universe (ADV20 >= $100M, cost_r <= 0.05) is negative in every cell in both halves.
- Check trades/session exceed the fit k. The check half holds more EVT-eligible rows (more liquid reaction-day names
  per season), and tau was fixed on FIT.

## Pick 31f in detail
| | FIT (OOF) | CHECK (once) |
|---|---|---|
| trades / per session | 361 / 3.44 | 1,782 / 6.46 (8.78 per traded session) |
| win | 0.468 | 0.452 |
| avg R (per 2u) / per 0.25-dATR unit | +0.0041 / +0.0082 | **-0.0425 / -0.085** |
| avg R w/o best day / best-day share | -0.014 / 4.30 (**1 day**: 2025-07-29) | -0.049 / n/a (total < 0) |
| total R / R per session | +1.5 / +0.009 | -75.7 / -0.274 |
| worst day / worst day per trade-session | -6.39 / -1.08 | -7.41 / -0.844 |
| day-clustered t | +0.09 | **-2.61** |
| avg R without 2025-04-03..04-09 | +0.0041 (OOF has no April) | n/a (no such dates) |
| long / short | +0.004 (353) / -0.004 (8) | -0.046 (1,667) / +0.004 (115) |
| SPY up / flat / down | +0.026 / +0.015 / -0.024 | -0.018 / -0.009 / -0.106 |
| sub-halves | A +0.038 / B -0.012 | first half -0.038 / second half -0.047 |
| earnings-season / off-season sessions | +0.002 (319) / +0.019 (42) | -0.043 (1,521) / -0.038 (261) |
| RD rows / RD+1 rows | +0.004 (179) / +0.004 (182) | -0.044 (803) / -0.041 (979) |
| random control (same name-session-side) | -0.071 (t -1.78) | -0.020 (t -1.52) |
| signal minus random | +0.075 | **-0.023** |
| median hold / stop share | 45 min / 9.4% | 45 min / 7.1% |
| bias diagnostic (signal-close fill, no borrow, no surcharge) | +0.008 | -0.039 |

- Earnings-season session = >= 5 lab names on RD that day. That gives 89 of 170 FIT sessions and 160 of 276 CHECK
  sessions.
- The round-4 cost fixes cost the pick about 0.004R/trade, measured by the bias diagnostic. Removing them would not
  change the verdict.

## BARS check (pick 31f)
| bar | value | pass |
|---|---|---|
| check avg R > 0 | -0.0425 | no |
| check avg R w/o best day > 0 | -0.049 | no |
| fit avg R > 0 (OOF) | +0.0041 | yes (barely; 1-day carried) |
| >= 2 trades/session on check | 6.46 | yes |
| no look-ahead | see below | yes |
| BEATS: > +0.0836, w/o best day > +0.0734, R/session > 0, t >= 3.716 | -0.0425, -0.049, -0.274, -2.61 | no |

**Tier: FAIL.** It is not TIER B either, because check -0.0425 < -0.02.

## What was built
- **Module** `research/ultimate_1119/modules/ULT-31.py`, plus:
  - `ULT-31_model.json`: the frozen 31f model, with a 31-feature scaler, sign-stable ridge weights (21 features
    kept), tau 0.01269 and univ EVT;
  - `ULT-31_symbols.json`: ETF and LEV lists, copied from ULT-20.
- The module follows the round 1-4 interface: LabStrategy `type: lab`, two entries in one file ("-S" = short),
  GEOM "S" (2u catastrophic stop) with `time_stop_min: 45`, and window 10:00-15:00.
- **Earnings state.** `earn_state()` is shared by the backtest and live.
  - It uses ULT-28's reaction-day rules.
  - Live reads `MCF_EARN_CAL` and `MCF_DAILY_CLOSES`, with closes dated before today only.
  - EVT exposes `SYMBOLS` (today's RD / RD+1 names) for `symbols: module`.
  - Missing files give an empty state: EVT makes no trades, and in ALL the earnings features are 0.
- **LIVE GAPS (they do not matter, since it fails):**
  - The live lab frame has no `symbol` column. The per-symbol earnings state, is_ETF and no-LEV-short need a runner
    extension or SYMBOL_HINT.
  - There is no adv20 and no sector column (both z -> 0).
  - There is no daily-close file, and the report hour is needed (the same as ULT-28/30).
- **Smoke test** `round4/ULT-31/test_module.py`: 5 tests, all passing. They cover:
  - LabStrategy long and short sides with a toy model, and the 2u stop;
  - fail safe without SPY context, and EVT without earnings state;
  - the frozen model running under LabStrategy;
  - the single-day live build (bars from 09:35, indicators clamped to the frames' 09:50 start) matching the month
    batch;
  - point-in-time truncation at bars 8 / 20 / 40;
  - the live STATE path matching the frame e_* columns;
  - EVT trading RD / RD+1 rows only, and no short of TQQQ;
  - the earnings-table point-in-time test: amc gives RD the next session; REACT appears only on RD+1, from closes
    <= RD; later closes leave it unchanged; RD rows carry no REACT; blocked-date events are dropped whole.
- **Backtest** `round4/ULT-31/bt.py` reuses ULT-11's sector map, month frame, chassis, tau calibration, ridge / GB
  export and stats, and ULT-20's flow.
  - The freeze order was enforced:
    - fitsel.json and the model JSON were frozen at 09:18:12Z;
    - check data was built afterwards;
    - check was scored once at 09:21:15Z;
    - asserts tie the sha256 of the model and module to fitsel.json;
    - check_once.json cannot be rewritten.
- **Locked block:**
  - pyarrow filters exclude it on daily closes, 1-minute bars and SPY;
  - `no_locked()` runs on every frame, row table, earnings state and walk;
  - events whose RD-1 / RD / RD+1 touch the block are dropped (for example RD 2025-03-03).
- **Forbidden columns** (win_*, r_*, *heat*) are dropped before features and asserted absent.
- **FIT-stage earnings state** reads only report dates and closes <= 2025-09-30.
  - Caveat: e_pre on 2025-09-26..30 misses October reports.
  - The earnings table was fetched after the fact, so rare date revisions are not modelled.

## Implementation choices (fixed before any scoring)
- **Rows** are the union of ALL and EVT per (bar, name, side). EVT gets its own scaler and models.
- **Target:** decision close -> the 5-minute close at tod+45, with LR8, the x1.5 RD surcharge before 10:30 and borrow
  (5 / 8 bp in RD-1..RD+1, 1.2 / 3 bp otherwise), winsorised +-4.
- **RS:** a leave-one-month-out ridge refit for each training month of the fold. A feature is kept when its sign
  equals the full-fold sign in >= 80% of the refits. In the 2025-05 fold, which has 3 training months, that means
  3 of 3. Dropped features get weight 0.
  - Kept counts per fold for 31f: 14 / 15 / 27 / 22 / 17 of 31.
- **GB on ALL** trains on a seeded 2M-row subsample when a fold has more rows. EVT uses all rows.
- **EVT tau** = k entries per earnings-season session on the training months.

## Bias caveats (all favour the candidate; it fails anyway)
- Today's symbol list (survivorship, which flatters longs).
- Today's ETB flag.
- The borrow fee is an estimate.

## Rule-change context (owner 2026-11-02)
- Both halves are scored with one fixed rule set: LR8 costs and the round-4 chassis. No live rule change falls inside
  them.
- The 4-day earnings blackout (owner 2026-10-07) has been in force through the whole live record, so no live
  comparison exists for earnings-window trading.

## Leads (diagnostic, not candidates)
- The only positive check cells are 31g / 31h, the EVT GB books. Their shorts are +0.199 (n 53) and +0.071 (n 130).
  - Both cells were negative on fit, so this is a check-only observation and must not be selected from.
  - It echoes ULT-20, where the GB short books were slightly positive on check.
- Within the EVT universe, random bars on the pick's names / sessions / sides lose -0.020 on check. The reaction-day
  universe itself has no positive base at TX-45 under this cost model. That fits ULT-29's base-gate finding and
  ULT-30's random-control finding (random RD+1 bars +0.051 check) only partly: the two universes and windows differ.

Files:
- `round4/ULT-31/fit_grid.json`, `fitsel.json`, `check_once.json`, `check_plateau.json`, `check_trades.csv.gz`
- `bt.py`, `test_module.py`
- `modules/ULT-31.py`, `ULT-31_model.json`, `ULT-31_symbols.json`

Educational only — not financial advice.
