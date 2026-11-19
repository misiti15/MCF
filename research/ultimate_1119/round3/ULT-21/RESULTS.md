Educational only — not financial advice

# ULT-21 ETF-RANK — learned ranker inside equity-basket ETFs, LONG (short exposure via inverse funds) (round 3)

**Tier: FAIL.** Not BEATS, not A, not B. CHECK-INFORMED (universe choice, PLAN sec. 0.5 i).
The fit pick **21d** (ridge, k 4, 45-min time exit) lost on walk-forward fit (OOF **-0.044R/trade**, t -1.81,
3.2/session). Scored once on check it lost again: **-0.012R/trade** (w/o best day -0.015, t -1.15, 5.7/session,
total -19.0R over 276 sessions). It was **worse than random entries** on the same ETF-sessions in both halves
(fit -0.055R, check -0.015R). All 8 configurations are negative on check. Nothing here can be salvaged by re-picking.

## In plain words
- The idea: equity-basket ETFs are the one universe where dips reverted out of sample (WB4 / ULT-12 anchor), and random
  entries there are about break-even. A small model trained on fit data might find more of those good entries than
  WB4's single rule.
- It did not. The model never beat random entries on the same funds and days. Random entries were about 0R
  (fit +0.011, check +0.003); the model's picks were -0.044 (fit) and -0.012 (check).
- Why, as far as we can tell: (1) the pre-registered cost cap (cost_r <= 0.08 with u = 0.25 x daily ATR) leaves only the
  high-ATR funds, mostly 2-3x leveraged ones (OIH, GDXU, NUGT, TECL, SOXL, KORU, SPXL ...; about 10-60 funds per bar, and
  fewest in quiet months). The unlevered index ETFs where WB4's dip edge sits mostly fail that cap. (2) The ridge weights
  are small and point toward trend (from-open distance +, VWAP distance +, DI +, RSI14 -). That is not WB4's dip
  geometry, and the TX-45 target is noise-dominated (per-bar SD ~0.36R vs. mean -0.016R).
- Lesson: on these funds the WB4 edge seems to be a narrow, specific event (a sharp 15-min dip after a calm hour). A
  general ranker trained on every bar learns trend and volatility, not that event. This is the same failure as ULT-11
  on stocks, now on ETFs too. The next step that could help is the event-conditioned ranker (ULT-20: rank only bars
  where the dip trigger already fired), not a wider ranker.

## Build (faithful to round3/PLAN.md sec. 3 "ULT-21")
- **Module** `research/ultimate_1119/modules/ULT-21.py` + `ULT-21_model.json` (frozen fit model: scaler, ridge weights,
  tau, exit) + `ULT-21_universe.json` (EQB list, leverage, inverse flags, exposure groups). Numpy only at run time.
  `raw_features` / `eligible` / `predict_z` are the same code bt.py runs. Indicators via
  `mcf.research.arena.indicators.compute` (as WB4 / ULT-12). GEOM comes from the frozen pick (TX -> "S": 2u
  catastrophic stop + YAML time_stop_min 45, time_stop_min_r 99).
- **Live-symbol gap fixed in the module:** live LabStrategy frames carry no symbol column, but leverage / inverse flags
  and the inverse exemption need one. `_infer_symbol` finds it from the runner's per-symbol frame cache
  (`_LAB_FRAMES`, same index and closes). If there is no unique match, the module gives no signal (fail safe).
  Account-side and not in the module: <= 3 entries per bar, session cap 2k, one open lot per exposure group.
- **Smoke test** `round3/ULT-21/test_module.py`: 5 passed. Covers: fires under the live LabStrategy (`symbols: module`,
  `context: [spy_fo]`) with t05s1 levels; single-stock fund refused; no SPY -> nothing; leverage / inverse flags reach
  the features live; universal long filter blocks long-exposure funds but not inverse funds; frozen model runs; live
  single-day features = month batch; removing later bars leaves earlier rows unchanged (point-in-time).
- **Universe EQB** (167 names; `round3/ULT-21/make_universe.py`, names / fund types only, written before any fit
  scoring): the WB4 list (124) + 43 lab ETFs holding equity baskets (international / country / thematic, KORU, RAM ...).
  Excluded: 25 single-stock funds, 19 commodity, 7 crypto, 2 volatility, 7 bond, DBMF, QQQI. 43 exposure groups.
  (round3/universes.json did not exist when this was built. The EQB list lives in modules/ULT-21_universe.json. Other
  round-3 builders should reuse it, or compare against it.)
- **Rows:** EQB, ADV20 >= $30M (point-in-time), price >= $10, |gap| < 20%, cost_r <= 0.08, bars 10:30-15:00, universal long
  filter on long-exposure funds. **Build interpretation (fixed before fit):** inverse funds are exempt from that filter,
  because buying one is a short exposure, not a long into a falling tape.
- **Features (24):** ret1/3/6/12 in dATR, di_diff7, RSI2/5/14, VWAP / open / HOD / LOD distance in dATR, volumeRatio,
  ATR%, cost_r, leverage, inverse flag, spy_fo, spy_r30, 5 time blocks. z-scored on the training fold only, clipped
  +-5, NaN -> 0. Forbidden frame columns (win_*, r_long*, r_short*, *heat*) are dropped before features, with an assert.
- **Target:** TX-45 after-cost R per 2u (decision close -> 1-minute close at tod + 45 from the 1-minute cache, LR8 both
  legs), winsorised +-4. Long only, so no borrow fee applies.
- **Models:** RG = ridge alpha 1e4. GB = HistGBR(depth 2, 100 iterations, lr 0.05, leaf 2000, l2 1, seed 1119), exported
  to numpy trees and checked against sklearn (assert). Walk-forward folds 2025-05..09, each trained on all earlier FIT
  months. "Fit" = pooled OOF over 105 sessions. Final models are trained on all FIT and frozen (fitsel.json at
  2026-11-19T07:43Z, before any check frame was built; sha256 of bt.py, module, model and universe recorded and
  asserted at check).
- **Chassis:** pred > tau; <= 3 entries per bar; session cap 2k; one lot per symbol (max 2 per symbol-session, refire >= 30
  min after the exit); one open lot per exposure group. tau = FIT in-sample constant giving k/session with approximate
  45-min exits. Entry = OPEN of the 1-minute bar starting at the decision close; LR8 costs; T5 = t05s1 bracket around
  the decision close, 45-min cap, R per u; TX = 45-min time exit with a 2u catastrophic stop, R per 2u. Flat 15:50.
- **Locked block** never read: pyarrow filters on every 1-minute load, `no_locked()` asserts on frames, days and trades,
  MCF_HIST_ALLOW_LOCKED refused.

## Selection (FIT = walk-forward OOF, 105 sessions) — every configuration
Rank = fit total R minus best fit day, among configs with >= 2.0/session (eligible: 21c, 21d, 21g, 21h).

| cfg | model-k-exit | OOF /sess | OOF avg R | w/o best day | total R | total w/o best | t | fit A / B | CHECK plateau (after the single score): /sess, avg R, w/o best, t |
|---|---|---|---|---|---|---|---|---|---|
| 21a | RG-k2-T5 | 1.64 | +0.013 | +0.003 | +2.1 | +0.6 | 0.30 | +0.072 / -0.007 | 2.72, -0.043, -0.047, -2.17 |
| 21b | RG-k2-TX | 1.60 | -0.018 | -0.027 | -3.0 | -4.4 | -0.49 | -0.014 / -0.019 | 2.71, -0.023, -0.027, -1.59 |
| 21c | RG-k4-T5 | 3.31 | -0.050 | -0.057 | -17.3 | -19.2 | -1.50 | -0.069 / -0.040 | 5.79, -0.027, -0.030, -1.86 |
| **21d** | **RG-k4-TX** | **3.21** | **-0.044** | **-0.049** | **-14.7** | **-16.2** | **-1.81** | -0.056 / -0.037 | **5.74, -0.012, -0.015, -1.15** |
| 21e | GB-k2-T5 | 1.54 | -0.083 | -0.097 | -13.5 | -15.4 | -1.66 | -0.041 / -0.096 | 2.20, -0.039, -0.043, -1.23 |
| 21f | GB-k2-TX | 1.51 | -0.058 | -0.074 | -9.2 | -11.5 | -1.25 | -0.064 / -0.056 | 2.19, -0.021, -0.027, -0.92 |
| 21g | GB-k4-T5 | 2.79 | -0.098 | -0.112 | -28.6 | -31.8 | -2.40 | -0.106 / -0.095 | 4.46, -0.041, -0.045, -1.71 |
| 21h | GB-k4-TX | 2.74 | -0.048 | -0.062 | -13.9 | -17.3 | -1.58 | -0.057 / -0.046 | 4.40, -0.025, -0.028, -1.47 |

The only fit-positive config (21a, +0.013, 1.6/session) was not eligible, and it lost -0.043 on check. On check the
pick traded 5.7/session, not 4. Volatile check months had more funds pass the cost cap than the fit months tau was
calibrated on.

## The fit pick 21d, fit vs check (R per 2u = actual risk; per 0.25-dATR unit = 2x)

| | FIT OOF (105 sess) | FIT in-sample final model (170 sess, reported only) | CHECK (276 sess, scored once) |
|---|---|---|---|
| trades (/session) | 337 (3.21) | 680 (4.00) | 1,583 (5.74) |
| win | 0.457 | 0.494 | 0.476 |
| avg R (per 0.25-dATR) | **-0.044** (-0.087) | +0.001 | **-0.012** (-0.024) |
| avg R w/o best day | -0.049 | -0.012 | -0.015 |
| best-day share | n/a (total < 0) | 13.9 (**1 day**) | n/a (total < 0) |
| total R / per session | -14.7 / -0.140 | +0.6 / +0.004 | -19.0 / -0.069 |
| worst day / per trade-session | -4.47 / -1.17 | -4.53 / -0.99 | -4.72 / -0.77 |
| day-clustered t | -1.81 | 0.04 | **-1.15** (bar 3.68) |
| avg R without 2025-04-03..04-09 | -0.044 (no April in OOF) | -0.004 | n/a (no such dates) |
| SPY up / flat / down avg R | +0.007 / -0.070 / -0.178 | +0.035 / -0.046 / -0.032 | +0.055 / -0.054 / -0.070 |
| first / second half | -0.054 / -0.029 | +0.031 / -0.047 | -0.004 / -0.019 |
| fit sub-halves A / B | -0.056 / -0.037 | +0.029 / -0.045 | — |
| inverse-fund trades (avg R) | 36 (-0.123) | 65 (+0.044) | 71 (-0.002) |
| median hold / exit mix | 45 min / 327 time, 10 stop | 45 / 665 time, 15 stop | 45 / 1,561 time, 22 stop |
| same-name random control | +0.011 (282) | — | +0.003 (1,411) |
| **signal minus random** | **-0.055** | — | **-0.015** |
| bias diag (signal-close fill; long only, so no borrow) | -0.040 | — | -0.010 |
| most-traded | OIH, GDXU, TECL, NUGT, SMH | | GDXU, OIH, NUGT, TECL, SOXL, KORU |

Base rate of every eligible OOF bar (TX-45 proxy, decision-close entry, before the chassis): -0.016R.

## Bars
TIER A fails on fit avg R (-0.044 <= 0), check avg R (-0.012 <= 0) and check w/o best day (-0.015 <= 0). Volume
(5.7/session >= 2) and no look-ahead pass. BEATS fails on every return test and on t (-1.15 vs. 3.68). TIER B fails
(fit avg R <= 0). **FAIL.**

## Counting and context
- Configurations: 8 grid + 1 bias diagnostic = 9, all inside the pre-registered round-3 total. Cumulative N = 880 (t
  bar 3.68). Random controls are reported, not counted. The plateau diagnostic was scored only after check_once.json.
- Rule-change context: both halves are scored with one fixed rule set (today's LR8 costs, round-3 chassis). No live rule
  change falls inside them. WB4 went live 2026-11-17 (Testing E), after the CHECK window.
- Known biases (today's symbol list, which flatters longs; fills at the next-minute open) all favour the candidate, and
  it still lost. No borrow-fee question arises (long only; inverse funds are bought, never shorted).

## Files
`round3/ULT-21/bt.py` (fit | check | plateau), `fitsel.json` (frozen pick), `fit_grid.json`, `check_once.json`,
`check_plateau.json`, `check_trades.csv.gz`, `test_module.py`, `make_universe.py`; `modules/ULT-21.py`,
`modules/ULT-21_model.json`, `modules/ULT-21_universe.json`.

Educational only — not financial advice.
