Educational only — not financial advice

# ULT-10 regime-switch book (composite) — RESULTS: **FAIL**

Research only (ultimate_1119, PLAN.md sec. 3 "ULT-10"). No setup, exit, config, account or ledger change. Nothing committed.

**Verdict: FAIL** under the pre-registered deploy bar (PLAN sec. 6). The fit-selected config is **10d T50-fitsel**. It was
chosen because it had the highest fit total R (+9.7R), and it also had the best fit avg R without its best day
(−0.005). On fit it was barely positive: +0.004R/trade, 14.8 trades/session. It is −0.005 without its best day, and that
one day (2025-04-04, +22.5R) is 231% of the total, so the fit record is a **1 day** record.

Scored once on CHECK, 10d gives **−0.039R/trade, −0.042 without its best day, 20.8 trades/session, −224R total
(−0.81R/session)**. That misses TIER A, which needs check > 0. It also misses TIER B, which needs check > −0.02.

Random entries were drawn in the same symbol-sessions, with the same leg windows, sides and exits. They score +0.006 on
check (fit +0.003). So the routed rules pick bars that are **worse than random** on check. All 4 grid configs lose on
check (−0.024 to −0.039), so there is no plateau to rescue. The volume goal was met (15-25 trades/session, long and
short). The goal of trading in any market was not: on check the book loses on up, flat and down sessions alike.

## What was built
- **Module (live interface):** `research/ultimate_1119/modules/ULT-10-regime-switch-book.py`.
  - It uses the same interface as the deployed workbench modules (`SIDE`, `GEOM`, `LAYERS`, `mask(df)`,
    `stop_price(f, i)`) and loads with `type: lab` + `module:`.
  - The live `LabStrategy` runs one side and one exit geometry per setup. So the book deploys as **one lab setup per
    leg**, all pointing at this one file. The leg, T and the config set are parsed from the YAML setup name. For
    example, `ULT-10-T50b-L04` means T 0.50%, set b, leg ULT-04. LabStrategy names the module `lab_<setup name>`;
    ULT-05 already uses the same trick for its side.
  - Each leg needs `context: [spy_fo]`, `min_adv: 20000000`, `refire: true`, `refire_cooldown: 0`, the leg window,
    and `time_stop_min` = the leg HOLD with `time_stop_min_r: 99`.
  - Book-wide parts sit at account level: "one position per symbol across setups" is already a runner rule, and the
    day cap of 30 = `max_trades_per_day: 30` in a dedicated arena account.
  - The module thins each leg (max 2 per symbol-session; next hit ≥ (hold + 30)/5 bars). The live approximation
    cannot enforce "max 2 per symbol-session" across legs. The backtest applies the exact book chassis.
  - Component rules are imported from the ULT-01..08 modules (THIN off). The ULT-09 rule is written in the book
    module (`ult09_mask`), because ULT-09's own module did not exist when this was built. It reproduces ULT-09's
    official fit result exactly: config 09c, 171 trades, +0.0674, +11.5R, the same numbers as ULT-09's
    `fitsel.json`.
- **Smoke test:** `research/ultimate_1119/ULT-10-regime-switch-book/test_module.py` (3 tests, all pass). It checks
  that:
  - all 9 legs × 2 sets × 2 T values load and run under the live `LabStrategy`, with the right side and geometry;
  - the ULT-07 leg fires on an afternoon dip with SPY +1% from its open, gives t05s1 levels, and does **not** fire on
    the same dip on a flat tape;
  - the leg fails safe without SPY context;
  - the regime labels come out right (flush is tested before down; spy_r30 before 10:20 counts as "not flush").
- **Backtest:** `bt.py` and `score.py`.
  - Signals come from the module's own `component_mask` on the lab frames, with the regime from `spy_s930` and
    `spy_r30` only.
  - The 1-minute exit walk is checked against ULT-01's walk: 3,886/3,886 rows give an identical exit price and kind.
  - Costs: LR8.
  - R is booked per unit of risk: time-exit (TX) legs are divided by their 2R catastrophic stop, as in
    `bench.cost_r` and ULT-01. ULT-02 and ULT-06 booked TX per 0.25-ATR unit in their own reports, so their TX figures
    there are 2× the per-risk scale used here.
  - Book chassis, exact: each day is processed in time order (ties: ADV20 descending, then leg order
    02, 04, 09, 03, 05, 07, 01, 06, 08). One lot per symbol across the book. Re-entry only ≥ 30 min after the exit.
    Max 2 per symbol-session. Day cap 30. Flat by 15:50. All holds are ≤ 45 min.

Routing as built (point-in-time, at each decision bar; spy_s930 = `spy_fo`, spy_r30 from `spy_fo` 30 min earlier):

| State | Condition | Legs |
|---|---|---|
| flush | spy_r30 < −T | 02 |
| down | else spy_s930 ≤ −T | 04, 09 |
| up | else spy_s930 ≥ +T | 03, 05 long side, 07 |
| flat | otherwise | 01, 06, 08 |

Component configs used:
- Set a (first-listed): 01a, 02a, 03a, 04a, 05a, 06a, 07a, 08a, 09a.
- Set b (fit-selected, from each component's `fitsel.json`): 01f, 02k, 03b, 04j, 05h, 06a, 07a, 08g, 09c.

Faithfulness notes:
- ULT-09's window 15:20 and ULT-07/08's 15:15/15:20 are capped at 15:00 because the frames and the live lab stop at
  15:00. The component agents did the same.
- ULT-05h was selected on both sides, but only its long side is used, as the PLAN says.

## Fit (2024-10 + 2025-03..09, 170 sessions) — all 4 grid configs

| config | trades | /session | win | avg R | avg R w/o best day | best-day share | total R | R/session | worst day | up / flat / down avg R |
|---|---|---|---|---|---|---|---|---|---|---|
| 10a T30-first | 3458 | 20.3 | 49.2% | −0.025 | −0.031 | n/a (total < 0) | −87.1 | −0.51 | −25.4 | +0.034 / −0.035 / −0.080 |
| 10b T30-fitsel | 2386 | 14.0 | 50.5% | −0.002 | −0.011 | n/a | −4.5 | −0.03 | −18.2 | +0.007 / −0.033 / +0.023 |
| 10c T50-first | 2815 | 16.6 | 49.7% | −0.013 | −0.019 | n/a | −36.5 | −0.21 | −17.0 | +0.019 / −0.048 / −0.019 |
| **10d T50-fitsel** | 2514 | 14.8 | 50.8% | **+0.004** | **−0.005** | **231% (1 day)** | **+9.7** | +0.06 | −12.7 | +0.007 / −0.044 / +0.051 |

**10d on fit, more detail:**
- Without the 2025-04-03..04-09 crash week: +0.001.
- Median hold: 30 min.
- Side split: long 2,131 trades at −0.010; short 383 trades at +0.081.
- ULT-06 dominates: 1,454 of 2,514 trades, at −0.021.

**Uncapped diagnostics** (no day cap; never used for selection):
- 10a: +0.013, 53/session.
- 10b: +0.004, 24/session.
- 10c: +0.060, 41/session.
- 10d: +0.045, 24/session (+0.023 without its best day).
- The uncapped figures are higher because the crash-week days add uncapped trades. The cap exists to stop exactly
  that kind of dominance.

## Check (2025-10-01..2026-11-04, 276 sessions) — 10d scored ONCE

| trades | /session | win | avg R | avg R w/o best day | best-day share | total R | R/session | worst day | median hold |
|---|---|---|---|---|---|---|---|---|---|
| 5739 | 20.8 | 47.1% | **−0.039** | **−0.042** | n/a (total < 0) | −224.4 | −0.81 | −28.8 (2026-03-03) | 30 min |

Splits of the 10d check score:
- **Day type** (SPY 09:30→15:59 ±0.30%; this end-of-day label is used for reporting only):
  - up: 1,897 trades at −0.027
  - flat: 2,216 trades at −0.011
  - down: 1,626 trades at −0.091
- **First / second half of check:** −0.065 / −0.010 (split at the middle session).
- **By routed state:**
  - flat: 4,287 trades at −0.033 (−143R)
  - up: 922 trades at −0.003
  - flush: 331 trades at −0.072
  - down: 199 trades at −0.277 (−55R)
- **Side split:** long 4,478 trades at −0.037; short 1,261 trades at −0.047.
- **By leg** (trades, avg R, total R):

| leg | trades | avg R | total R | note |
|---|---|---|---|---|
| 06 | 3225 | −0.043 | −139.4 | the main drag |
| 09 | 130 | −0.435 | −56.5 | two days, 2026-03-03 and 02-17, give −51R |
| 02 | 331 | −0.072 | −23.7 | |
| 08 | 34 | −0.170 | −5.8 | |
| 05 | 598 | −0.007 | −4.2 | |
| 03 | 277 | −0.002 | −0.6 | |
| 04 | 69 | +0.019 | +1.3 | |
| 01 | 1028 | +0.002 | +2.1 | |
| 07 | 47 | +0.051 | +2.4 | |

**Random control** (same symbol-session, same leg window, side and exit; random intake-U bar; 3 seeds; no chassis):

| half | random avg R | signals avg R |
|---|---|---|
| check | +0.006 (seeds +0.000 / +0.008 / +0.010) | −0.039 |
| fit | +0.003 | +0.004 |

The book adds nothing over random on fit and loses 0.045R/trade against random on check.

**Plateau diagnostic** (all 4 configs on check, after the single score; never used to re-select):

| config | /session | avg R | avg R w/o best day | total R |
|---|---|---|---|---|
| 10a | 24.5 | −0.024 | −0.027 | −161 |
| 10b | 20.5 | −0.035 | −0.039 | −199 |
| 10c | 21.5 | −0.034 | −0.037 | −202 |
| 10d | 20.8 | −0.039 | −0.042 | −224 |

## Recorded-quote replay (third opinion): not run
- `mcf.replay.store.available_days()` returns no session packs locally (`data/replay` holds only spreads.json).
  `research/reps2` is not in this checkout.
- Deploying the book in a replay would need a 9-leg dedicated account config.
- With a clear check FAIL on all 4 configs, the replay could not change the tier.

## Configurations
- **ULT-10 grid:** 4, as pre-registered.
- **Uncapped diagnostics:** 4 computed. The PLAN counts 1 for this candidate, so 3 are extra. They are reported and
  were never used for anything.
- **ULT-09 fit grid:** I re-ran its 8 configs, which ULT-09 already counts, to get set b's leg 09. The results are
  identical to ULT-09's own grid.
- **Check:** 1 single score, plus the 4-config plateau diagnostic and random controls.
- **Earlier work in this folder** (reported alongside): ULT-01..09 grids, and 574 evidence configs.

## Why it failed (honest reading, and what can be salvaged)
- **A composite cannot beat its parts.** Every component failed on check: ULT-01..09 are all FAIL, and none has a check
  avg R > 0 with ≥ 2/session. Routing by the in-day SPY state cannot add edge that the parts do not have. The router
  also hands most of the volume to the flat-state legs, and ULT-06 there is 56% of all check trades, at −0.043.
- **Selection noise, as WAVE1 warned:**
  - On fit, the fit-selected set b beat the first-listed set a (10d > 10c, 10b > 10a).
  - On check the order reverses: set a beats set b at both T values.
  - The "down-session specialist" shorts (04 and 09) went from +0.09 / +0.16 on fit to +0.02 / −0.43 on check.
- **The regime idea is not refuted.** The in-day state labels behaved as designed: each state routed the legs it was
  meant to. The failure is in the component triggers: the check bars they pick are worse than random bars in the same
  names. That is the part to work on.
- **What might be salvaged for a later round** (backlog only, not deployable):
  - The legs that were not negative on check, 01, 04 and 07, are each too thin and too small to matter on their own.
  - The book chassis itself (one lot per symbol across legs, a book-level day cap, routing by spy_s930/spy_r30) is
    built, tested and reusable. It can be pointed at any future component that passes on its own.
- **Rule-change context:** this is a 2-year history backtest only. No live window is used, so no `ledger.jsonl` rule
  change mixes into these numbers. Universe survivorship (today's 1,226 symbols) flatters longs, and borrow fees are
  not modelled. Both caveats make the true result no better than shown.

## Files
- `research/ultimate_1119/modules/ULT-10-regime-switch-book.py`: the live-ready module.
- `research/ultimate_1119/ULT-10-regime-switch-book/`:
  - `bt.py`, `score.py`, `test_module.py`
  - `fit_grid.json` (ULT-09 grid + 4 book configs + uncapped)
  - `fitsel.json` (frozen 05:46 UTC, before any check data was loaded)
  - `check_once.json`, `check_trades.csv`, `random_control.json`, `check_plateau.json`
- Run order:
  1. `python bt.py WORK sig fit`
  2. `python bt.py WORK walk fit`
  3. `python score.py WORK fit`
  4. `python bt.py WORK sig check` (refuses to run without `fitsel.json`)
  5. `python bt.py WORK walk check`
  6. `python score.py WORK check`

Educational only — not financial advice.
