Educational only — not financial advice

# ULT-02 tape-flush washout long (S4) — RESULTS (Workbench Mechanic, 2026-11-19)

Research only: no setup, exit, config, account or ledger change; nothing committed. Pre-registration: `../PLAN.md` sec. 3
(ULT-02), selection sec. 5, deploy bar sec. 6. **TIER: FAIL** (check avg R −0.091, w/o best day −0.185, 1.83
trades/session; it misses TIER A on three counts and TIER B, which needs check avg R > −0.02).

## What was built
- **Module** `research/ultimate_1119/modules/ULT-02-tapeflush-washout-long.py`. It uses the deployed workbench
  interface (`SIDE`, `GEOM`, `LAYERS`, `mask(df)`) and loads with `type: lab` + `module:` like L3-…-WB5. Context
  `[spy_fo]`. spy_r30 is computed inside the mask from `spy_fo`: (1+fo_t)/(1+fo_{t−30})−1. The row 30 minutes earlier
  must exist, otherwise the value is NaN and nothing fires. This matches SPY 1-minute closes exactly; 5 of 5 spot
  checks agree to 4 decimals. The backtest calls the module's own mask (`make_mask` per grid config), so the module and
  the backtest are the same code. Frozen values = 02k.
- **Smoke test** `test_module_smoke.py` (2 passed). The module runs under the live `LabStrategy` with SPY peers and
  fires only after a synthetic SPY flush. It gives the same decision bar on bars cut at the signal (no look-ahead).
  Stop = 2R (0.5 × ATR), no target, timed exit 45 min.
- Live YAML that would match (NOT applied): `type: lab`, `window: [1030, 1500]`, `min_adv: 20000000`, `context:
  [spy_fo]`, `geom: hold`, `r_atr_frac: 0.5` (2R catastrophic stop), `time_stop_min: 45`, `time_stop_min_r: 1e9`,
  `refire: true`, `refire_cooldown: 14`.
  - **Live approximations** (the engine has no exact equivalent):
    - The cooldown counts from the signal (75 min ≈ a 45-min hold + 30 min), not from the actual exit.
    - There is no "max 2 per symbol-session" and no per-setup day cap of 30.
    - Live R would be 0.5 × ATR, so live R figures would be about half of the research figures below, which use
      R = 0.25 × ATR.
- **Backtest** `bt.py` + `score.py`. The chassis follows the PLAN:
  - Intake U, lab frames, point-in-time ADV20 ≥ $20M, bar close 10:30–15:00.
  - Entry at the decision-bar close. Exits walked on 1-minute bars: stop first, gap-through at the worse price,
    flat 15:50.
  - One lot per symbol; re-entry ≥ 30 min after the exit; max 2 per symbol-session; day cap 30 (first by time, ties
    by ADV20).
  - LR8 costs: entry 1c + 1 bp × time-of-day multiplier; exit 1c + 1 bp except limit targets; +2c on stops.
  - TX results are in R = 0.25 ATR, not divided by the 2R stop, so the sign is unaffected.

## Configurations tried: 13 counted
- 12 grid configs (02a..02l) plus 1 uncapped diagnostic of the fit-selected config.
- Not counted: random controls, and the check-half plateau, which re-scores the same 12 configs after the single check
  scoring.
- Prior evidence work behind S4: movehunt long, 104 configs.

## FIT half (2024-10 + 2025-03..09, 170 sessions) — all 12 configs

| cfg | SPY_T | depth | exit | trades | /sess | win | avg R | avg R w/o best day | best-day share | total R | worst day | avg R ex 04-03..09 | med hold |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 02a | −0.30 | A | TX30 | 1682 | 9.89 | 0.482 | −0.068 | −0.083 | n/a | −115.1 | −27.5 | −0.032 | 30 |
| 02b | −0.30 | A | TX45 | 1676 | 9.86 | 0.479 | −0.063 | −0.086 | n/a | −106.0 | −47.8 | −0.026 | 45 |
| 02c | −0.30 | A | t1s1c45 | 1679 | 9.88 | 0.492 | −0.034 | −0.046 | n/a | −57.3 | −20.1 | −0.043 | 36 |
| 02d | −0.30 | B | TX30 | 720 | 4.24 | 0.531 | +0.004 | −0.030 | 829% **1 day** | +2.9 | −21.6 | +0.062 | 30 |
| 02e | −0.30 | B | TX45 | 711 | 4.18 | 0.522 | +0.060 | −0.003 | 105% **1 day** | +42.7 | −28.2 | +0.108 | 45 |
| 02f | −0.30 | B | t1s1c45 | 715 | 4.21 | 0.510 | −0.023 | −0.048 | n/a | −16.6 | −21.3 | +0.041 | 19 |
| 02g | −0.50 | A | TX30 | 769 | 4.52 | 0.477 | −0.048 | −0.096 | n/a | −36.8 | −27.5 | −0.009 | 30 |
| 02h | −0.50 | A | TX45 | 768 | 4.52 | 0.484 | −0.018 | −0.071 | n/a | −14.1 | −47.8 | −0.010 | 45 |
| 02i | −0.50 | A | t1s1c45 | 770 | 4.53 | 0.500 | −0.005 | −0.040 | n/a | −4.2 | −21.6 | −0.060 | 31 |
| 02j | −0.50 | B | TX30 | 352 | 2.07 | 0.548 | +0.058 | +0.015 | 76% **1 day** | +20.2 | −21.6 | +0.104 | 30 |
| **02k** | −0.50 | B | TX45 | 345 | 2.03 | 0.530 | **+0.129** | **−0.001** | **101% 1 day** (2025-04-04) | **+44.5** | −24.9 | +0.105 | 45 |
| 02l | −0.50 | B | t1s1c45 | 351 | 2.07 | 0.510 | −0.032 | −0.059 | n/a | −11.3 | −18.8 | +0.023 | 18 |

**Selection (PLAN sec. 5, pre-registered):** 02k is the config with the highest fit total R among configs with ≥ 2.0
trades/session. It was frozen in `fitsel.json` at 2026-11-19T05:06:16Z, before any check data was loaded.

How strong is 02k on fit?
- Even on fit, the record rests on one day: without its best session (2025-04-04, the tariff crash) avg R is −0.001,
  and that day's share is 101%.
- No config has a positive avg R w/o best day except 02j (+0.015).
- Ex the 04-03..09 week, depth B is positive (+0.06..+0.11) and depth A is negative.
- 02k by SPY day type (fit): up −0.579 (n 65) / flat +0.284 (n 52) / down +0.295 (n 228).
- Fit sub-halves: +0.150 / +0.087.
- Uncapped diagnostic (fit): 808 trades, +0.332 avg R, but +0.106 w/o best day and 75% best-day share (2025-04-07).

## CHECK half (2025-10-01..2026-11-04, 276 sessions) — 02k scored ONCE

| | trades | /sess | traded sess | win | avg R | avg R w/o best day | best-day share | total R | R/sess | worst day | med hold |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **02k check** | 505 | **1.83** | 43 | 0.485 | **−0.091** | **−0.185** | n/a (total < 0) | −46.1 | −0.167 | −37.7 | 45 |
| uncapped diag | 921 | 3.34 | 43 | 0.580 | +0.157 | −0.003 | 101% **1 day** (2026-06-09) | +144.7 | +0.524 | −60.5 | 45 |

- **SPY day type (check):** up −0.367 (n 6) / flat +0.059 (n 103) / down −0.126 (n 396).
- **Check sub-halves:** −0.185 (to 2026-02-25) / +0.090 (from 2026-02-26).
- **By month (avg R, n):**
  - Negative: 2025-10 −0.18 (102), 2025-11 −0.49 (54), 2025-12 −0.46 (40), 2026-02 −0.05 (99), 2026-05 −0.60 (4),
    2026-06 −0.24 (68), 2026-07 −0.26 (2), 2026-08 −0.57 (6), 2026-09 −1.28 (10).
  - Positive: 2026-01 +0.56 (58), 2026-03 +0.25 (18), 2026-04 +0.23 (25), 2026-10 +0.77 (19).
  - **4 of 13 months are positive; the fit evidence said "every ex-April month positive".**
- Fires on 43 of 276 sessions (16%), not "about half".

**Plateau (diagnostic only, after the single check scoring, never used to re-select)** (`check_grid.csv`): 11 of 12
configs are negative on check. The only positive one is 02i (+0.007, 386% best-day share, w/o best day −0.019). Every
config is negative w/o its best day (−0.019..−0.246). There is no plateau to rescue.

## vs random (same exit TX45, LR8 costs; each signal replaced by the mean of up to 3 draws)

| | signal | (a) same symbol-session, random window bar | (b) same moment (date, tod), random intake-U name |
|---|---|---|---|
| fit | +0.129 | −0.382 (signal − ctl +0.511) | **+0.136 (signal − ctl −0.007)** |
| check | −0.091 | −0.351 (+0.260) | −0.207 (+0.116) |

Reading:
- On fit, the "washout" selection added nothing over random names bought at the same flush moment (−0.007). The fit
  result was the SPY-bounce bet, not the name selection.
- On check the washout names did better than same-moment random names (+0.116), but the bounce itself lost (−0.207
  for random names). The +0.15R-over-control claim was not confirmed on fit, and it did not make money on check.

## Recorded-quote replay (third opinion): not run
- The replay needs session packs in `data/replay` (`mcf.replay.store.available_days()` returns none locally; the packs
  are built from the Alpaca SIP feed by the store-bars workflow), and runs take about 1 h per account.
- Disk is about 88% full.
- With the check result already a clear FAIL, the replay could not change the tier.
- The rule fires only on sessions where SPY falls more than 0.5% in 30 minutes, so recent live sessions would give few
  trades: October 2026 had 19 check trades.

## Notes / caveats (honest reporting)
- **Why the fit evidence (+0.189R) did not carry over:**
  - The movehunt S4 figure used one position per symbol with no day cap, no max-2 rule, entry at the next minute's
    open, price ≥ $5 and a 30-min exit with no stop.
  - The PLAN chassis caps at 30 entries a day, earliest first. On flush days that keeps the entries made while the tape
    is still falling and drops the later rebound entries. That is why the uncapped diagnostic looks better: +0.157
    check. Its one-day share is still 101%, so the edge lives in one or two crash-rebound sessions per half.
  - The thesis caveats ("a correlated bet on SPY bouncing", "below the multiple-testing bar") are exactly what failed.
- **Rule-change context:** pure historical backtest, no live window, so no ledger rule changes fall inside it.
- **Survivorship:** the frames universe is today's 1,226 lab symbols, which flatters longs. Even so, the check result is
  negative.
- **Locked block:**
  - 2024-11-01..2025-02-28 was never scored. Month lists exclude it, pyarrow filters exclude it on every 1-minute
    load, and every frame and trade list carries an assert.
  - One early exploratory command read SPY.parquet's `close` column unfiltered, to print the cache's first and last
    timestamps. No locked-block value was used or scored.
- Work files (candidates and trades, about 8 MB) were in the scratchpad and have been deleted; they can be rebuilt with
  `bt.py WORK cand|walk fit|check`.
- Files: `bt.py`, `score.py`, `fit_grid.csv`, `fitsel.json`, `check_once.json`, `check_trades.csv`, `check_grid.csv`,
  `test_module_smoke.py`, module above.

Educational only — not financial advice.
