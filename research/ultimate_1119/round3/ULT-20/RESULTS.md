Educational only — not financial advice

# ULT-20 EVR — event-conditioned learned ranker, long + short — ROUND 3 RESULT: **TIER A on paper, weak; not deployable (not BEATS)**

Research only. No account, setup, exit or config changed. Nothing committed. **CHECK-INFORMED** (uses the one-bar RSI
collapse L2 and the short pop / roll-over S1 / S2, round3/PLAN.md sec. 0.5).

## In plain words
- The model only ranked bars where at least one library trigger fired (5 long, 4 short, plus sector lag). It was trained
  on FIT only and tested walk-forward inside FIT (folds 2025-05..09).
- **Only 1 of the 12 pre-registered versions did well inside FIT**: 20a (ridge, k 4, liquid universe L1): +0.0425 R/trade,
  3.8/session, t 1.54. 9 of 12 were at or below zero once their best day is removed. 20a was frozen and scored once on CHECK.
- **CHECK: +0.0075 R/trade over 1,693 trades (6.1/session), +0.0052 without the best day, t = 0.55.** That clears the
  TIER A sign tests by a hair, but it is far below the benchmark (+0.0836) and about zero in practice.
- **It does not beat a random event bar on the same name and session.** On CHECK it beats a random bar from all eligible
  bars by +0.028 R, but it is **-0.026 R worse** than a random bar where a trigger fired. So the model adds nothing over
  the triggers themselves. In FIT it was +0.022 over a random trigger bar. That gain did not hold up out of sample.
- It is in effect a long-only "buy the trigger when SPY is rising" book (99% long). The largest weights are side-signed
  SPY-from-open and SPY 30-min change, plus DI. It makes money on SPY-up days (+0.058) and loses on SPY-down days (-0.081).
- The plateau check, run after the single check score and never used to choose, shows **11 of the 12 configs at or below
  zero on CHECK without their best day**. Only the pick is positive. The fit result looks like selection luck.
- Verdict: by the letter, TIER A (all four sign bars pass). By substance it is a weak setup (t 0.55, edge ≈ 0, below
  random trigger bars). Under the owner's "no weak setups", **do not deploy**. It is reported for completeness.

## Result of the fit pick 20a (RG ridge a=1e3, k 4, universe L1: ADV20 >= $100M, cost_r <= 0.05)
R per unit of actual risk (2u, u = 0.25 daily ATR). LR8 costs in. Next-minute-open fill. Borrow 1.2 bp of entry notional
(3 bp when the entry is < $20). Shorts only ETB, never leveraged / inverse / volatility funds.

| | OOF FIT (2025-05..09, 105 s) | In-sample all FIT (170 s, final model; reported only) | **CHECK (2025-10-01..2026-11-04, 276 s)** |
|---|---|---|---|
| trades (/session) | 396 (3.77) | 683 (4.02) | **1,693 (6.13)** |
| win | 0.520 | — | 0.502 |
| avg R (per 0.25-dATR unit) | +0.0425 (+0.085) | +0.0194 | **+0.0075 (+0.015)** |
| avg R w/o best day | +0.0322 | +0.0130 | **+0.0052** |
| best day / share | 2025-05-21 / 25.1% | — / 33.1% | 2026-03-10 / 31.9% (no 1-day tag) |
| total R (R/session) | +16.8 (+0.160) | — | +12.75 (+0.046) |
| total R w/o best day | +12.6 | — | +8.7 |
| worst day; worst day / trade-session | -2.71; -0.684 | — | -4.70; **-0.747** |
| day-clustered t | 1.54 | 0.80 | **0.55** |
| avg R without 2025-04-03..04-09 | +0.0425 (no OOF dates there) | +0.0323 | n/a (no such dates) |
| long / short (trades, avg R) | 388 +0.052 / 8 -0.401 | 669 +0.031 / 14 -0.530 | 1,676 +0.008 / 17 -0.082 |
| SPY up / flat / down avg R (EOD label) | +0.057 / +0.054 / -0.021 | — | +0.058 / +0.014 / **-0.081** |
| first / second half avg R | +0.034 / +0.051 | — | +0.022 / **-0.005** |
| fit sub-halves A (2025-05 OOF part) / B (06-09) | +0.039 (95) / +0.044 (301) | — | — |
| random entry, base (any eligible bar, same name-session-side) | -0.074 → signal - random **+0.117** | — | -0.021 → **+0.028** |
| random entry, event bar (any trigger bar, same name-session-side) | +0.020 → signal - random **+0.022** | — | +0.034 → **-0.026** |
| bias diagnostic: signal-close fill, no borrow | +0.0497 | — | +0.0147 |
| median hold; stop-out share | 45 min; 5.3% | — | 45 min; 4.3% |
| raw candidates (score > tau) / session | 7.2 | — | 17.4 (tau drift: 6.1 trades/s vs 4 targeted) |

Check month by month (avg R): 25-10 -0.072, 11 +0.123, 12 +0.054, 26-01 +0.034, 02 +0.010, 03 +0.013, 04 -0.048,
05 +0.044, 06 -0.059, 07 -0.024, 08 +0.037, 09 +0.013, 10 -0.002, 11 (3 days) +0.186. By hour: 10h +0.018 (526), 11h +0.021 (766),
12h -0.010, 13h -0.074, 14h +0.009.
Survivorship caveat: the result is ~99% long on today's symbol list, which favours longs. The survivorship-neutral read
(signal minus random event bar) is negative on CHECK.

## Bars (round3/PLAN.md sec. 6; cumulative N = 880, t floor sqrt(2 ln 880) = 3.68)
- TIER A: check avg R > 0 **yes** (+0.0075); w/o best day > 0 **yes** (+0.0052); fit (OOF) avg R > 0 **yes** (+0.0425);
  >= 2/session on check **yes** (6.13); no look-ahead **yes** (see below). → **TIER A (marginal)**.
- BEATS: avg R > +0.0836 **no**; w/o best day > +0.0734 **no**; total R/session > 0 yes; worst day / trade-session
  -0.747 >= -2.152 yes; t >= 3.68 **no** (0.55). → **does not beat the benchmark**.
- Deploy note for the Deploy stage / skeptic: not "clearly positive". The edge is about zero, t is 0.55, the second check
  half is negative, it is below random trigger bars, and 11/12 configs are flat to negative on check. Recommendation:
  **do not deploy**.

## Fit grid (walk-forward OOF inside FIT, 105 sessions; selection = highest OOF total R minus best day among >= 2/session)
The task text's rule (highest fit total R among >= 2/session) picks the same config (20a, +16.8).

| cfg | model-k-universe | trades/s | avg R | w/o best day | total R | total w/o best | t | long / short trades | long / short avg R | sub-half A / B | cands/s |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **20a** | **RG-k4-L1 (pick)** | 3.77 | +0.0425 | +0.0322 | +16.8 | **+12.6** | 1.54 | 388 / 8 | +0.052 / -0.401 | +0.039 / +0.044 | 7.2 |
| 20b | RG-k4-L2 | 3.41 | +0.0120 | -0.0002 | +4.3 | -0.1 | 0.35 | 344 / 14 | +0.014 / -0.028 | +0.027 / +0.005 | 8.1 |
| 20c | RG-k10-L1 | 8.82 | +0.0125 | +0.0041 | +11.6 | +3.8 | 0.63 | 898 / 28 | +0.021 / -0.263 | +0.024 / +0.009 | 17.8 |
| 20d | RG-k10-L2 | 8.81 | -0.0246 | -0.0335 | -22.8 | -30.3 | -1.01 | 882 / 43 | -0.023 / -0.067 | -0.018 / -0.027 | 19.5 |
| 20e | LG-k4-L1 | 4.00 | +0.0089 | -0.0049 | +3.7 | -2.0 | 0.33 | 401 / 19 | +0.009 / +0.015 | -0.055 / +0.025 | 6.5 |
| 20f | LG-k4-L2 | 4.16 | -0.0253 | -0.0393 | -11.0 | -16.9 | -0.77 | 414 / 23 | -0.023 / -0.059 | -0.043 / -0.021 | 7.1 |
| 20g | LG-k10-L1 | 9.18 | -0.0114 | -0.0163 | -11.0 | -15.6 | -0.78 | 925 / 39 | -0.009 / -0.065 | -0.005 / -0.013 | 15.3 |
| 20h | LG-k10-L2 | 9.57 | -0.0317 | -0.0424 | -31.9 | -42.0 | -1.55 | 953 / 52 | -0.036 / +0.052 | -0.030 / -0.032 | 17.2 |
| 20i | GB-k4-L1 | 3.56 | -0.0477 | -0.0564 | -17.9 | -20.8 | -1.92 | 321 / 53 | -0.034 / -0.133 | -0.093 / -0.035 | 7.4 |
| 20j | GB-k4-L2 | 4.02 | +0.0104 | -0.0050 | +4.4 | -2.1 | 0.34 | 340 / 82 | +0.029 / -0.065 | -0.038 / +0.025 | 11.4 |
| 20k | GB-k10-L1 | 8.79 | -0.0186 | -0.0235 | -17.1 | -21.2 | -1.24 | 720 / 203 | +0.002 / -0.092 | -0.022 / -0.018 | 22.2 |
| 20l | GB-k10-L2 | 11.29 | +0.0133 | -0.0012 | +15.8 | -1.4 | 0.59 | 956 / 229 | +0.019 / -0.009 | -0.029 / +0.023 | 23.8 |

## Check plateau (all 12 final models on CHECK, run AFTER check_once.json; diagnostic, never used to select)
| cfg | trades/s | avg R | w/o best day | total R | t | long / short trades | long / short avg R |
|---|---|---|---|---|---|---|---|
| 20a (pick) | 6.13 | +0.0075 | +0.0052 | +12.8 | 0.55 | 1676 / 17 | +0.008 / -0.082 |
| 20b | 5.63 | -0.0123 | -0.0160 | -19.1 | -0.73 | 1445 / 109 | -0.009 / -0.054 |
| 20c | 15.92 | -0.0135 | -0.0155 | -59.3 | -1.38 | 4278 / 115 | -0.016 / +0.078 |
| 20d | 14.32 | -0.0127 | -0.0153 | -50.1 | -1.11 | 3648 / 303 | -0.011 / -0.038 |
| 20e | 6.80 | -0.0269 | -0.0288 | -50.4 | -2.17 | 1839 / 38 | -0.031 / +0.189 |
| 20f | 6.16 | -0.0444 | -0.0472 | -75.5 | -2.56 | 1668 / 33 | -0.044 / -0.047 |
| 20g | 17.68 | -0.0232 | -0.0247 | -113.4 | -2.52 | 4772 / 107 | -0.025 / +0.052 |
| 20h | 16.34 | -0.0347 | -0.0368 | -156.7 | -2.93 | 4396 / 114 | -0.035 / -0.019 |
| 20i | 6.08 | +0.0022 | -0.0006 | +3.7 | 0.19 | 1363 / 316 | -0.005 / +0.032 |
| 20j | 4.35 | +0.0048 | -0.0015 | +5.8 | 0.29 | 882 / 319 | -0.007 / +0.037 |
| 20k | 15.90 | -0.0052 | -0.0068 | -23.0 | -0.68 | 3208 / 1179 | -0.010 / +0.008 |
| 20l | 11.30 | -0.0042 | -0.0069 | -13.2 | -0.47 | 2510 / 609 | -0.008 / +0.010 |

What can be salvaged (for the next round, not a claim): the GB models' short books are slightly positive on check
(+0.008..+0.037 over 300-1,200 shorts). The k 10 configs show that more volume quickly drifts negative. Ranking among
trigger bars did not beat the triggers alone. A future attempt should test triggers directly (gated per trigger in both
fit halves, as ULT-24 does) instead of learning a context model over them.

## Build, look-ahead and fidelity
- Module `modules/ULT-20.py` (+ `ULT-20_model.json` frozen fit model: 29-feature scaler, ridge weights, tau 0.0886,
  univ L1; `ULT-20_symbols.json`: ETF list + LEV fund list from fund names only). Runs under the live LabStrategy (two
  `type: lab` entries, side from the setup name, GEOM "S" 2u catastrophic stop, YAML time_stop_min 45).
  Smoke test `round3/ULT-20/test_module.py`: 4/4 pass. It covers both sides firing only on their own events, toy model,
  stop geometry, fail-safe without SPY, frozen model runs, single symbol-day (live shape) = batch build, a
  **truncation test** (features / events at bar t unchanged when the frame is cut at t), and no leveraged-ETF shorts.
- bt.py uses the module's own build / side_rows / side_features / predict (the same code live runs) and reuses the
  round-2 ULT-11 pipeline (sector map, chassis, tau calibration, stats). Forbidden columns (win_*, r_*, *heat*) are
  dropped before features and asserted absent. Locked block never read (no_locked asserts on every frame, 1-min load,
  headtail and trade list).
- Order: fitsel.json frozen 2026-11-19T07:46:31Z (sha256 of bt.py, module, model JSON, symbols JSON). The check sector map
  and check frames were built after that. Check scored once at 07:49:39Z (check_once.json). Plateau ran after that.
- Interpretation choices (faithful, stated): one pooled model for both sides (side enters via is_long and the signed
  features), 29 features (PLAN "~26"). E5 is the event in the row's side. tau is calibrated in-sample on the training
  months through the chassis with approximate exits (ULT-11 method). Training rows for LG / GB were all rows (<= 0.8M, no
  subsample needed).
- Live gaps (as ULT-11 / ULT-17): the live lab frame has no adv20 (log ADV → z 0), no sector columns (E5 never fires
  live), no symbol column (is_ETF → 0 unless SYMBOL_HINT is set). A runner extension would be needed before any live use.
- Known biases that favour the candidate: today's symbol list (survivorship; 99% long book) and ETB flag from today.
  Borrow fee is in. The bias diagnostic (signal-close fill, no borrow) adds about +0.007 R on check.

## Configurations
12 grid configs + 1 bias diagnostic, as pre-registered in round3/PLAN.md sec. 4 (already inside the cumulative N = 880).
No amendments. Random controls (base and event bar) are reported and not counted.

## Rule-change context (owner 2026-11-02)
Both halves were scored with one fixed rule set (today's LR8 costs, round-3 chassis). No live rule change applies inside
them. Live ledger changes during CHECK (11-12 LR8 cost model, 10-28 Primary sizing, 10-30 Testing cost filter, 11-17
TSZ1 / SPYEXIT, setup moves) concern live accounts, not this backtest.

Files: `round3/ULT-20/{bt.py, test_module.py, fitsel.json, fit_grid.json, check_once.json, check_plateau.json,
check_trades.csv.gz}`, `modules/ULT-20.py`, `modules/ULT-20_model.json`, `modules/ULT-20_symbols.json`.

Educational only — not financial advice.
