Educational only — not financial advice

# ULT-11 LR-RANK — learned ranker (wide features), long + short — ROUND 2 RESULT: **FAIL**

Research only. No account, setup, exit or config was changed. Nothing committed.

## In plain words
- A ridge / boosted-tree model was trained on the FIT months only, using 43 point-in-time features. It scored every
  5-min bar for a long and a short 30- or 45-minute time-exit trade. The setup took the better side when the score was
  above a threshold. All 12 pre-registered versions **lost money out-of-fold inside FIT** (avg R -0.034 to -0.096).
- The fit pick (11g: ridge a=1e5, 45-min exit, k = 8) was frozen and then scored **once** on CHECK:
  **-0.0275 R/trade over 3,047 trades (11.0/session)**, avg R w/o best day -0.031, day-clustered t = -2.30.
- **It has no edge over random entries.** On check it is +0.0004 R better than a random entry on the same names and
  sessions (OOF fit: +0.031). The model learned too little: the scores mostly pick long trades on names that move a
  lot, and those lose about as much as random entries on the same names.
- All 12 configs are negative on check as well (plateau check, run after the single check score): -0.010 to -0.033.

## Result of the fit pick (R per unit of actual risk = 2u; u = 0.25 daily ATR; LR8 costs + 1.2 bp borrow on shorts in)

| | OOF FIT (2025-05..09, 105 sessions) | In-sample all FIT (170 s, final model; reported only) | CHECK (2025-10-01..2026-11-04, 276 s) |
|---|---|---|---|
| trades (/session) | 706 (6.72) | 1,397 (8.22) | **3,047 (11.04)** |
| win | 0.482 | 0.469 | 0.464 |
| avg R (in 0.25-dATR units) | -0.0408 (-0.082) | -0.0203 (-0.041) | **-0.0275 (-0.055)** |
| avg R w/o best day | -0.0498 | -0.0288 | **-0.0309** |
| best day / share | 2025-08-01 / n/a (total < 0) | 2025-04-07 / n/a | 2026-10-15 / n/a |
| total R (R/session) | -28.8 (-0.274) | -28.4 (-0.167) | -83.7 (-0.303) |
| worst day; worst day / trade-session | -5.94; -0.841 | -12.07; -1.434 | -9.24; -0.825 |
| day-clustered t | -1.60 | -1.04 | **-2.30** |
| avg R without 2025-04-03..04-09 | -0.0408 (no trades there) | -0.0179 | n/a (not in check) |
| long / short (trades, avg R) | 664 -0.035 / 42 -0.137 | 1,351 -0.022 / 46 +0.018 | 2,936 -0.028 / 111 -0.020 |
| SPY up / flat / down avg R | -0.018 / -0.049 / -0.076 | +0.014 / -0.019 / -0.080 | +0.032 / -0.031 / -0.121 |
| first / second half avg R | -0.054 / -0.028 | -0.005 / -0.044 | -0.027 / -0.028 |
| random entry, same name-session-side-exit | -0.0718 (signal - random **+0.031**) | — | -0.0279 (signal - random **+0.0004**) |
| bias diagnostic: signal-close fill, no borrow | -0.0219 | — | -0.0243 |
| median hold | 45 min | 45 min | 45 min |

The bias diagnostic shows the next-minute-open fill + borrow fee cost about 0.003 (check) to 0.019 (OOF) R per trade.

## Bars (round2/PLAN.md sec. 6)
- TIER A: check avg R > 0 **no** (-0.0275); w/o best day > 0 **no**; fit (OOF) avg R > 0 **no** (-0.041); >= 2/session
  yes (11.0); no look-ahead yes (see below). -> **not TIER A**.
- BEATS: needs TIER A + check avg R > +0.0836, w/o best day > +0.0734, t >= 3.65 (N = 774) -> **no** (t = -2.30).
- (Round-1 TIER B, fit > 0 and check > -0.02: also no.) **Tier: FAIL.**

## Fit grid (walk-forward OOF inside FIT, 105 sessions; selection = highest OOF total R minus best day among >= 2/session)

| cfg | model-h-k | trades/s | avg R | w/o best day | total R | total w/o best day | t | long / short trades | long / short avg R | raw candidates/s |
|---|---|---|---|---|---|---|---|---|---|---|
| 11a | R3-h30-k8 | 8.19 | -0.0859 | -0.0926 | -73.8 | -78.2 | -4.13 | 478 / 382 | -0.069 / -0.107 | 24 |
| 11b | R3-h30-k20 | 20.53 | -0.0463 | -0.0493 | -99.7 | -105.4 | -3.71 | 1354 / 802 | -0.032 / -0.070 | 72 |
| 11c | R3-h45-k8 | 7.21 | -0.0909 | -0.0989 | -68.8 | -73.3 | -3.96 | 629 / 128 | -0.057 / -0.256 | 49 |
| 11d | R3-h45-k20 | 18.39 | -0.0635 | -0.0682 | -122.7 | -128.9 | -4.88 | 1638 / 293 | -0.041 / -0.192 | 116 |
| 11e | R5-h30-k8 | 7.99 | -0.0958 | -0.1054 | -80.3 | -86.7 | -4.30 | 604 / 235 | -0.070 / -0.161 | 22 |
| 11f | R5-h30-k20 | 20.14 | -0.0446 | -0.0503 | -94.3 | -104.6 | -3.39 | 1603 / 512 | -0.036 / -0.070 | 62 |
| **11g** | **R5-h45-k8 (pick)** | 6.72 | -0.0408 | -0.0498 | -28.8 | **-34.4** | -1.60 | 664 / 42 | -0.035 / -0.137 | 39 |
| 11h | R5-h45-k20 | 17.01 | -0.0491 | -0.0539 | -87.7 | -94.5 | -3.33 | 1677 / 109 | -0.041 / -0.180 | 94 |
| 11i | GB-h30-k8 | 6.91 | -0.0532 | -0.0638 | -38.6 | -45.3 | -2.01 | 161 / 564 | +0.020 / -0.074 | 41 |
| 11j | GB-h30-k20 | 22.18 | -0.0383 | -0.0425 | -89.2 | -97.4 | -2.88 | 1214 / 1115 | -0.014 / -0.065 | 228 |
| 11k | GB-h45-k8 | 6.45 | -0.0465 | -0.0527 | -31.5 | -35.4 | -1.37 | 276 / 401 | -0.043 / -0.049 | 303 |
| 11l | GB-h45-k20 | 25.46 | -0.0344 | -0.0389 | -91.9 | -102.3 | -2.00 | 1405 / 1268 | -0.011 / -0.061 | 732 |

## Plateau check (all 12 final models on CHECK, run only after check_once.json; never used to re-select)
Every config is negative: 11a -0.010 (11.5/s), 11b -0.018, 11c -0.012, 11d -0.014, 11e -0.012, 11f -0.016,
11g -0.028, 11h -0.017, 11i -0.033, 11j -0.024, 11k -0.020, 11l -0.028; t from -0.85 to -3.78. Longs and shorts are
both negative in every config. There is no hidden winner in the grid.

## What was built (faithful to the PLAN, with notes)
- Universe U2 (price >= $10, ADV20 >= $50M, |gap| < 20%, cost_r <= 0.08), every decision bar 09:50-15:00, universal
  side filters, shorts ETB only (universe.csv, today's flag). 43 features, all as listed in the PLAN (time + 5 blocks;
  gap, gap/ATR%; fromOpen, VWAP, HOD, LOD, PDH, PDL in dATR; RSI14/5/2, RSI slope; ret 1/3/6/12 bars in dATR via exact
  time lags; volume ratio, buy pressure, flow3, wicks; SMA20/50 distance, SMA20 slope; ATR%; log ADV20; cost_r; SPY fo
  and r30; QQQ fo and VWAP; breadth and breadth change; sector ETF fo, r30, name fo minus beta x sector fo,
  sector-missing flag). z-scored with training-fold mean/sd, clipped +-5, NaN -> 0.
- Target: after-cost R of a time exit h min later (decision close -> 5-min close at tod + h, frames + headtail rows), LR8
  both legs + borrow for shorts, u units, winsorised +-4. Ridge exact from month-accumulated X'X/X'y; HistGBR on a fixed
  2M-row subsample (seed 1119). The numpy tree evaluator in the module was checked against sklearn (atol 1e-6).
- tau = in-sample threshold giving k entries/session **through the chassis** (approximate exits at entry + h) on the
  training months. Note: out of sample the predictions drift above tau (raw candidates 22-732/session against k), so the
  realised volume is set mostly by the chassis caps (3/bar, 2k/session, one lot, refire, 2/symbol).
- Scoring: entry at the next 1-minute open, 2u catastrophic stop, time exit at h, flat 15:50, R per 2u.
- Walk-forward folds 2025-05..09 (each trains on all earlier FIT months); final model retrained on all FIT; model JSON
  + fitsel.json (sha256 of bt.py, module, model) frozen at 2026-11-19T06:43:51Z **before** any check frame or
  feature was built. The sector map for FIT used only daily rows <= 2025-09-30. The check sector map was built inside
  the check stage.
- Look-ahead guard: frames win_* / r_long* / r_short* and every *heat* column are dropped before features are
  computed. Features use only the row's own and earlier same-day bars, context at the same bar, and prior-session
  daily values (ATR, gap, ADV20, PDH/PDL, sector map from strictly prior sessions). Locked block never read: pyarrow
  filters on daily, headtail and 1-minute loads, no_locked() asserts everywhere, MCF_HIST_ALLOW_LOCKED refused.
- **Live module gap** (does not matter for a FAIL; must be fixed before any live use): the live lab frame has no
  adv20 or sector-ETF columns, so the module sees them as missing (z = 0, sector-missing = 1). That is not what the
  backtest saw. It needs a runner extension.
- Remaining biases favour the candidate: today's symbol list (flatters longs; the book is 96% long) and today's ETB
  flag.

## Configurations
13 for ULT-11: 12 grid + 1 bias diagnostic, as pre-registered. Cumulative N stays at the planned 774 (t floor 3.65).
Random-entry controls and the plateau check are reported, not counted.

## Files
Under research/ultimate_1119/round2/ULT-11/: bt.py (pipeline), fit_grid.json, fitsel.json (frozen pick), check_once.json,
check_plateau.json, check_trades.csv.gz, test_module.py (3 passed under the live LabStrategy).
Module: research/ultimate_1119/modules/ULT-11.py + ULT-11_model.json (frozen 11g model; for the record, not for deployment).

## Rule-change context
The 2-year halves are scored with one fixed (today's) rule set, so no live rule change falls inside them (round-1
RESULTS.md lists the live-window ledger changes).

Educational only — not financial advice.
