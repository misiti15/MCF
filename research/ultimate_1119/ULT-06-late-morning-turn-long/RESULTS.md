Educational only — not financial advice

# ULT-06 late morning-turn long — RESULTS (Workbench Mechanic, 2026-11-19)

Research only: no setup, exit, config, account or ledger change; nothing committed. Pre-registration: `../PLAN.md`
sec. 3 (ULT-06), selection sec. 5, deploy bar sec. 6. **TIER: FAIL.** Check avg R is −0.091 and −0.099 without the best
day. That misses TIER A, and it also misses TIER B, which needs check avg R > −0.02. All 8 grid configs are negative
on check, so there is no plateau.

## What was built
- **Module** `research/ultimate_1119/modules/ULT-06-late-morning-turn-long.py`.
  - It uses the deployed workbench interface (`SIDE`, `GEOM` "hold", `LAYERS`, `mask(df)`) and loads with `type: lab`
    + `module:`.
  - Context `[spy_fo]`. The backtest calls the module's own `make_mask`, so the module and the backtest run the same
    code. Frozen values = 06a.
  - **New low:** one of the last 6 decision bars (the current bar included) has a 5-min low strictly below the running
    low of day as of the bar before. That bar must close at 09:55 or later. The running LOD is
    `close − dist_lod_atr × atr_d`, so it includes 09:30–09:50.
    - Hand-checked on A 2025-03-04: new lows at 10:05 and 10:10; the flag stays on through 10:35 and is off at 10:40.
  - **SPY turn:** `(1+fo_t)/(1+min fo_{09:50..t}) − 1 ≥ 0.10%`. On history frames the minimum is built from the
    (date, tod) table, so a missing row on one symbol cannot drop a SPY low. It matches the context table to 1e-5.
  - **No look-ahead:** every input comes from bars closed at the decision bar, plus prior-day ATR and ADV20.
- **Smoke test** `test_module_smoke.py` (2 passed).
  - Runs under the live `LabStrategy` with SPY peers on a synthetic turn day. It fires inside [1050, 1130] with a 2R
    stop (0.5 × ATR), no target and a 30-min time stop.
  - On bars cut at the signal it gives the same decision bar (no look-ahead).
  - It does not fire when SPY makes no turn.
- **Live YAML that would match (NOT applied):** `type: lab`, `module: …/ULT-06-late-morning-turn-long.py`,
  `window: [1050, 1130]`, `min_adv: 20000000`, `context: [spy_fo]`, `geom: hold`, `r_atr_frac: 0.5`,
  `time_stop_min: 30`, `time_stop_min_r: 1e9`, `refire: true`, `refire_cooldown: 11`.
  - **Live approximations:**
    - The cooldown counts from the signal (55 min ≈ 30-min hold + 30 min), not from the exit.
    - There is no live max-2 per symbol-session and no day cap of 30.
    - Live R would be 0.5 × ATR, so live R figures would be about half of the R figures here.
- **Backtest** `bt.py` + `score.py`: the ULT-02 chassis with the PLAN rules.
  - Intake U, point-in-time ADV20 ≥ $20M, lab frames.
  - Entry at the decision-bar close. Exits walked on 1-minute bars: 2R stop checked first, gap-through at the worse
    price, time exit at 30 / 45 min, flat 15:50.
  - One lot per symbol; re-entry ≥ 30 min after the exit; max 2 per symbol-session; day cap 30.
  - LR8 costs, with +2c on stops. R = 0.25 × ATR.
  - The locked block is never read: the month list excludes it, and pyarrow filters and asserts guard every load.

## Configurations tried: 9 counted
- 8 grid configs (06a..06h) plus 1 uncapped diagnostic of the fit-selected config.
- Not counted: random controls, and the check plateau, which re-scores the same 8 configs after the single check
  scoring.
- Prior evidence: morning_low_1116 (post hoc) and movehunt long (104 configs).

## FIT half (2024-10 + 2025-03..09, 170 sessions) — all 8 configs

| cfg | W | RCL | exit | trades | /sess | win | avg R | avg R w/o best day | best-day share | total R | worst day | avg ex 04-03..09 | up / flat / down avg |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **06a** | 1050-1130 | 0.3 | TX30 | 1895 | 11.15 | 0.512 | +0.032 | **−0.009** | **127% 1 day** (2025-04-04) | **+61.1** | −24.9 | −0.027 | −0.008 / −0.086 / +0.199 |
| 06b | 1050-1130 | 0.3 | TX45 | 1895 | 11.15 | 0.531 | +0.024 | +0.005 | 78% **1 day** | +45.0 | −44.7 | −0.004 | +0.009 / −0.051 / +0.117 |
| 06c | 1050-1130 | 0.5 | TX30 | 391 | 2.30 | 0.496 | +0.051 | −0.081 | 247% **1 day** | +19.9 | −8.3 | −0.113 | −0.060 / −0.136 / +0.244 |
| 06d | 1050-1130 | 0.5 | TX45 | 391 | 2.30 | 0.535 | +0.013 | −0.027 | 306% **1 day** | +4.9 | −8.5 | −0.053 | −0.076 / −0.006 / +0.091 |
| 06e | 1030-1200 | 0.3 | TX30 | 3247 | 19.10 | 0.464 | −0.077 | −0.102 | n/a | −251.5 | −30.6 | −0.087 | −0.031 / −0.118 / −0.086 |
| 06f | 1030-1200 | 0.3 | TX45 | 3247 | 19.10 | 0.472 | −0.085 | −0.100 | n/a | −277.0 | −44.7 | −0.074 | +0.021 / −0.133 / −0.159 |
| 06g | 1030-1200 | 0.5 | TX30 | 888 | 5.22 | 0.465 | −0.055 | −0.115 | n/a | −49.2 | −36.8 | −0.093 | −0.018 / −0.098 / −0.054 |
| 06h | 1030-1200 | 0.5 | TX45 | 888 | 5.22 | 0.506 | −0.046 | −0.073 | n/a | −40.5 | −33.3 | −0.039 | +0.015 / +0.022 / −0.158 |

**Selection (PLAN sec. 5):** 06a has the highest fit total R among configs with ≥ 2.0 trades/session. It was frozen in
`fitsel.json` at 2026-11-19T05:26:51Z, before any check data was loaded.

How strong is 06a on fit? Weak even here:
- Without its best session (2025-04-04, the tariff crash) avg R is −0.009, and that day's share is 127%.
- Ex the 04-03..09 week it is −0.027.
- Fit sub-halves: +0.099 / −0.026.
- Uncapped diagnostic (fit): 2,991 trades, +0.281 avg R, but +0.005 w/o best day (98% share, the same 04-04).
- The wide window (W2, which adds 10:30–10:50 and 11:30–12:00) loses on fit in every config. That fits the
  morning_low_1116 note that the 10:25 window itself is null.

## CHECK half (2025-10-01..2026-11-04, 276 sessions) — 06a scored ONCE

| | trades | /sess | traded sess | win | avg R | avg R w/o best day | best-day share | total R | R/sess | worst day | med hold |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **06a check** | 3988 | 14.45 | 251 | 0.458 | **−0.091** | **−0.099** | n/a (total < 0) | −362.0 | −1.31 | −57.8 | 30 |
| uncapped diag | 5684 | 20.59 | 251 | 0.450 | −0.102 | −0.123 | n/a | −582.4 | −2.11 | −127.7 | 30 |

- **SPY day type (check; end-of-day label, reporting only):** up +0.055 (n 1180) / flat −0.018 (n 1523) / down −0.311
  (n 1285). The rule fires on every kind of day, but the "turn" fails on down days: the morning low is not the day's
  low.
- **Check sub-halves:** −0.095 (to 2026-04-13) / −0.086 (from 2026-04-14). It is stable, and stably negative.
- **By month (avg R, n):**
  - Positive: 2025-11 +0.195 (164), 2026-05 +0.113 (267), 2026-09 +0.017 (232), 2026-11 +0.115 (20).
  - Negative: 2025-10 −0.301 (372), 2025-12 −0.308 (267), 2026-01 −0.021 (422), 2026-02 −0.075 (312), 2026-03
    −0.023 (449), 2026-04 −0.050 (392), 2026-06 −0.278 (262), 2026-07 −0.123 (348), 2026-08 −0.179 (157), 2026-10
    −0.093 (324).
  - 4 of 14 months are positive.
- **Volume:** the volume target is met easily (14.4 trades/session, 91% of sessions traded). The edge is not there.

**Plateau (diagnostic only, after the single check scoring, never used to re-select)** (`check_grid.csv`):
- Every config is negative on check (−0.027..−0.091) and negative without its best day (−0.039..−0.103).
- The least bad is 06g (W2, RCL 0.5, TX30): −0.027, 6.2/session.
- Deeper reclaims (RCL 0.5) lose less than 0.3 in both windows, but none reaches the TIER B line.

## vs random (same exit TX30, LR8 costs, random bars inside the 10:50–11:30 window)

| | signal | (a) same symbol-session, random window bar | (b) same moment (date, tod), random intake-U name |
|---|---|---|---|
| fit | +0.032 | +0.182 (signal − ctl −0.151) | +0.031 (signal − ctl +0.001) |
| check | −0.091 | +0.087 (signal − ctl −0.178) | −0.061 (signal − ctl −0.029) |

Reading:
- The name-level trigger adds nothing over random names bought at the same moment: +0.001 on fit, −0.029 on check.
- The same names bought at a random late-morning bar did better than at the trigger bar, by −0.15 / −0.18 in both
  halves. Entering right after a new low and a 0.3-ATR bounce buys the local pop, which then gives back. This is the
  opposite of the thesis.
- The SPY-turn bet itself (control b) was flat on fit and −0.061 on check.

## Recorded-quote replay (third opinion): not run
- `mcf.replay.store.available_days()` returns no session packs locally; `data/replay` holds only spreads.json.
- The check result is already a clear FAIL, so a replay could not change the tier.

## Notes / caveats (honest reporting)
- **The build is faithful to the PLAN rule:** every clause is implemented as written, and the only live
  approximations are the refire/cap ones listed above. The FAIL is the candidate's own, not the build's.
- **Survivorship bias** (today's symbol list) flatters longs, so the true result is likely worse.
- **Borrow fees** are not relevant (long only).
- **Why the evidence did not carry over:** the morning_low_1116 effect (SPY +15 bps at +90 min) is an index-level
  drift over 90 minutes.
  - Per name with a 30/45-min hold, the trigger catches the first bounce off a fresh low, and that bounce mean-reverts.
  - On down days (32% of check trades) the low keeps breaking (−0.31).
  - The movehunt finding that washout depth alone has no after-cost edge holds here too, and the turn confirmation
    did not supply one.
- **Salvage leads (next round only, not tested, would be new counted configs):**
  - (1) Index-level only: trade SPY/SPXL on the turn with a 90-min hold, closer to the evidence.
  - (2) Require the SPY session label to be above a point-in-time "not down" gate (spy_s930 > −0.30%), since the
    down-day bucket carries the loss. Down-day losses are known only at the end of the day, so the gate would need its
    own pre-registered test.
- **Rule-change context:** pure historical backtest with no live window, so no ledger rule changes fall inside it.
- **Files:** `fit_grid.csv`, `fitsel.json`, `check_once.json` (with by-month figures), `check_trades.csv`,
  `check_grid.csv`.
