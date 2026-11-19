Educational only — not financial advice

# ULT-32 FLOW-DIP — results (round 4, LONG, D2, CHECK-INFORMED)

Research only. No setup, exit, config or account change. Nothing committed.

**Verdict: TIER B (near miss), so FAIL against the goal. Do not deploy.**
- The fit pick, 32f, trades 1.71/session on check. That is below the 2.0/session TIER A floor.
- Its check t is 1.98 against a 3.72 bar, and its check avg R is +0.062 against the +0.0836 bar.
- Leg D, the volume step, loses in both halves. It is the reason the pick misses.
- The two "flow" parts do hold out of sample again (E +0.110, M +0.124 on check). Together, without D, they make only ~1.0-1.2 trades/session.

## What was built
- **Module:** `research/ultimate_1119/modules/ULT-32.py`, with universes in `modules/ULT-32_symbols.json`.
  - It runs under the live LabStrategy as three YAML entries, one per leg. Each entry takes its leg from the setup name's suffix -E / -M / -D.
  - Smoke test: `round4/ULT-32/test_module.py`, 6 passed. It covers live signals for legs E and M, t05s1 / t1s1 levels, the allow-lists, min_adv, the SPY long filter, the no-SPY fail-safe, the slow-slide non-trigger, and point-in-time truncation of every feature and of the mask.
- **Backtest:** `round4/ULT-32/bt.py`.
  - It reuses ULT-28's 1-minute walk and LR8 cost_R, and ULT-23's stats.
  - Features come from the live module.
  - Forbidden columns (win_*, r_long*, r_short*, *heat*) are dropped and asserted absent.
  - The locked block is never read (pyarrow filters plus asserts).
- **Legs, exactly as in PLAN sec. 3:**
  - E = WB4 exact, t05s1.
  - M = one-bar RSI14 collapse on non-fund stocks with ADV20 >= A and price >= $20, 10:15-15:00, t1s1.
  - D = WB4-A dip on the same stocks, 14:00-15:00, t05s1. No ATR floor, as the plan lists D's conditions.
  - Earnings blackout on M and D: report date or reaction day within ±4 sessions. It uses dates only, which are scheduled ahead.
  - One lot per symbol across legs. M takes a bar it shares with D. Refire >= 30 min after the exit, max 2 per symbol-session, day cap 30.
  - Long only, so no borrow fee applies. The reaction-day surcharge never applies: the blackout keeps M and D off reaction days, and E trades ETFs.
- **Dissection cost caps (my choice; the live setups have none):** ST7-FD at cost_r <= 0.15 (the Testing filter value), WB4 at 0.10.

## Selection (FIT only; frozen 2026-11-19T09:18:53Z, before any check data was built)
- Rule (PLAN sec. 5): the highest fit total R minus the best fit day, among configs with >= 2.0 trades/session.
- Only 32f and 32h were eligible. **Pick: 32f = A $500M, RMAX 30, leg D on.** 32f scored 27.01 and 32h scored 26.68.
- After the freeze, the module's pick constants were set to 32f (RMAX 35 → 30). This is the only change to the module after the freeze.

| cfg | label | fit /sess | fit avg R | w/o best day | best-day share | total R | worst day / trade-sess | t | sub-half A / B |
|---|---|---|---|---|---|---|---|---|---|
| 32a | A1B-R30-Doff | 1.48 | +0.221 | +0.183 | 0.27 | +55.8 | -0.57 | 4.23 | +0.254 / +0.006 |
| 32b | A1B-R30-Don | 1.76 | +0.198 | +0.163 | 0.26 | +59.1 | -0.93 | 3.58 | +0.230 / +0.045 |
| 32c | A1B-R35-Doff | 1.68 | +0.185 | +0.150 | 0.28 | +52.8 | -0.64 | 3.58 | +0.225 / -0.001 |
| 32d | A1B-R35-Don | 1.95 | +0.167 | +0.136 | 0.26 | +55.5 | -1.03 | 3.16 | +0.205 / +0.031 |
| 32e | A500M-R30-Doff | 1.59 | +0.188 | +0.148 | 0.30 | +50.7 | -0.61 | 3.58 | +0.218 / +0.008 |
| **32f** | **A500M-R30-Don** | **2.17** | **+0.114** | **+0.080** | **0.36** | **+42.2** | **-3.50** | **1.59** | **+0.144 / +0.021** |
| 32g | A500M-R35-Doff | 1.98 | +0.153 | +0.120 | 0.28 | +51.4 | -0.70 | 3.04 | +0.185 / +0.033 |
| 32h | A500M-R35-Don | 2.53 | +0.097 | +0.067 | 0.36 | +41.7 | -4.01 | 1.47 | +0.123 / +0.032 |

- **Fit pick, 32f:**
  - Best day 2025-04-10. Worst day -15.17R, in April 2025.
  - Without 2025-04-03..04-09: +0.123 (n 246).
  - SPY up / flat / down: +0.212 / +0.099 / +0.042.
  - Median hold 19 min. Exits: 206 target, 117 time, 46 stop.
- **Fit by leg (32f):** E +0.216 (1.21/session), M -0.051 (0.18/session), D -0.006 (0.78/session).
- **The fit edge sits in sub-half A.** Every cell's sub-half B (Jun-Sep 2025) is ~0, from -0.001 to +0.045.
- **Fit random control (32f):** random -0.045, signal minus random +0.159.
  - E: +0.216 vs +0.046.
  - M: -0.051 vs -0.050.
  - D: -0.006 vs -0.186.
- **Bias diagnostic (32f):** filling at the signal close gives +0.119, vs +0.114 at the next-minute open.

## CHECK — scored once on 32f (276 sessions, 2025-10-01..2026-11-04)

| trades | /session | win | avg R | w/o best day | best-day share | total R | R/session | worst day | worst day / trade-sess | t (day-clustered) |
|---|---|---|---|---|---|---|---|---|---|---|
| 471 | **1.71** | 0.597 | **+0.0616** | +0.0496 | 0.21 (2026-06-17, +6.0R) | +29.0 | +0.105 | -5.13 | -1.98 | **1.98** |

- **Splits:**
  - SPY up / flat / down: +0.073 / +0.002 / +0.117.
  - First half +0.074, second half +0.049.
  - Without 2025-04-03..04-09: unchanged, because check holds no such dates.
- **Trades and costs:**
  - Median hold 45 min. Exits: 259 time, 172 target, 40 stop.
  - Bias diagnostic: +0.063 at the signal close.
  - Uncapped: identical, so the day cap never binds.
- **By leg:**
  - E: +0.110, 0.82/session, t 2.87, w/o best day +0.096.
  - M: +0.124, 0.42/session, t 1.80, w/o best day +0.084.
  - **D: -0.078, 0.47/session, t -1.38.**
- **Random control:** random -0.042, so signal minus random is **+0.103**.
  - E: +0.110 vs +0.065.
  - M: +0.124 vs -0.102.
  - D: -0.078 vs -0.171.
- **Without the earnings blackout (description only):**
  - 2.02/session, +0.062, t 1.92.
  - M falls to +0.077.
  - So the blackout helps leg M slightly and costs the volume that would have passed the 2/session floor.

**Bars:**

| Bar | Result | Status |
|---|---|---|
| TIER A: check avg R > 0 | +0.062 | met |
| TIER A: check avg R w/o best day > 0 | +0.050 | met |
| TIER A: fit avg R > 0 | +0.114 | met |
| TIER A: >= 2 trades/session on check | 1.71 | **missed** |
| BEATS: check avg R > 0.0836 | +0.062 | **missed** |
| BEATS: w/o best day > 0.0734 | +0.050 | **missed** |
| BEATS: worst day / trade-session >= -2.152 | -1.98 | met |
| BEATS: t >= 3.72 | 1.98 | **missed** |

→ **TIER B.**

## Check plateau (diagnostic, after the single score; never re-selects)

| cfg | /sess | avg R | w/o best day | t | E / M / D avg R |
|---|---|---|---|---|---|
| 32a A1B-R30-Doff | 1.04 | +0.135 | +0.123 | 3.77 | +0.110 / +0.226 / – |
| 32b | 1.25 | +0.102 | +0.092 | 2.97 | … / +0.226 / -0.053 |
| 32c | 1.42 | +0.107 | +0.094 | 3.32 | … / +0.103 / – |
| 32d | 1.64 | +0.086 | +0.074 | 2.78 | … / +0.103 / -0.053 |
| 32e | 1.24 | +0.115 | +0.099 | 3.29 | … / +0.124 / – |
| 32f (pick) | 1.71 | +0.062 | +0.050 | 1.98 | … / +0.124 / -0.078 |
| 32g A500M-R35-Doff | 1.98 | +0.086 | +0.072 | 2.88 | … / +0.069 / – |
| 32h | 2.45 | +0.055 | +0.042 | 2.00 | … / +0.069 / -0.078 |

- **Leg D lowers every cell, in both halves.**
- No cell meets BEATS. The only cell with t > 3.72 is 32a, at 1.04/session.
- The only cell with >= 2/session is 32h, at +0.055 and t 2.0.
- The combination that would look best on check (E + M without D, A $1B) is exactly the 0.8 + 0.2/session pair we already knew. It cannot reach 2/session.

## Part 1 dissection (FIT selects nothing; check columns added only after the single score)
ST7-FD and WB4 run through the round-4 chassis.

| ablation | fit /sess | fit avg R | fit A / B | check /sess | check avg R | check t |
|---|---|---|---|---|---|---|
| ST7-base (reference) | 0.94 | -0.143 | -0.288 / +0.047 | 2.23 | +0.094 | 2.41 |
| drop cross-below-50 | 29.6 | -0.072 | | 30.0 | -0.027 | |
| drop RSI <= 30 | 29.8 | -0.044 | | 30.0 | -0.037 | |
| drop fromOpen <= -1% | 4.46 | -0.105 | | 7.44 | -0.001 | |
| drop buyPressure > 0 | 3.69 | -0.092 | | 7.38 | +0.022 | |
| hour 09:50-11:00 | 0.59 | -0.240 | | 1.37 | +0.128 | 2.31 |
| hour 11:00-13:30 | 0.18 | +0.141 | | 0.49 | -0.056 | |
| hour 13:30-15:00 | 0.17 | -0.107 | | 0.37 | +0.165 | 1.67 |
| ADV $95-300M | 0.57 | -0.129 | | 1.29 | +0.086 | 1.90 |
| ADV $300M-1B | 0.28 | -0.320 | | 0.65 | +0.080 | 1.62 |
| **ADV >= $1B** | 0.09 | **+0.326** | +0.286 / +0.361 | 0.29 | **+0.160** | 2.18 |
| exit t05s1 | 0.94 | -0.158 | | 2.23 | +0.058 | |
| exit TX-45 | 0.94 | -0.113 | | 2.23 | +0.052 | |
| WB4-base (reference) | 1.41 | +0.219 | +0.249 / -0.041 | 0.82 | +0.110 | 2.87 |
| **drop dip** | 10.1 | -0.007 | | 13.6 | -0.049 | -3.44 |
| **drop DI** | 2.31 | +0.077 | | 2.03 | +0.001 | |
| drop falling-hour guard | 1.48 | +0.212 | | 1.00 | +0.074 | |
| drop ATR floor | 1.55 | +0.210 | | 0.86 | +0.117 | 2.97 |
| hour 10:30-12:30 | 1.85 | -0.031 | | 2.77 | -0.005 | |
| hour 12:30-14:00 | 1.30 | +0.038 | | 1.54 | -0.041 | |
| hour 14:00-15:00 (= base) | 1.41 | +0.219 | | 0.82 | +0.110 | |
| other basket ETFs (not WB4) | 0 | – | | 0.19 | -0.041 | |
| WB4 unleveraged | 0.48 | +0.305 | | 0.06 | +0.300 | |
| (complement: leveraged) | 1.04 | +0.199 | | 0.76 | +0.096 | |
| exit t1s1 | 1.40 | +0.194 | | 0.82 | +0.128 | 2.47 |
| exit TX-45 | 1.39 | +0.046 | | 0.82 | +0.086 | |

**Read:**
- **ST7-FD.** Only the >= $1B tier is positive in both halves (fit sub-halves A and B too). Every other part flips sign between halves. ST7-FD's check result rests on the 09:50-11:00 block and the < $1B tiers, and those lose on fit.
- **WB4.** Three layers carry it: the 15-minute dip, the DI guard and the 14:00-15:00 hour. The ATR floor and the falling-hour guard add little; dropping the ATR floor even keeps check flat at +0.117.
- **Every way of adding volume loses.** That covers the other hours, the other basket ETFs, a dropped dip and a dropped DI.
- **WB4's fit edge sits in sub-half A.** A = Oct-24 + Mar-May-25 at +0.249; B = Jun-Sep-25 at -0.041. Without 2025-04-03..04-09 it is +0.196.

## Configurations and the t bar
- **This candidate counts 34:**
  - 8 grid;
  - 23 dissection ablations;
  - **2 dissection reference bases (amendment: ST7-base and WB4-base were scored too, so they are counted)**;
  - 1 bias diagnostic (inside the plan's round-4 diagnostics line).
- **Cumulative N = 998** (996 + 2). sqrt(2 ln 998) = 3.717, so the bar stays at 3.72.
- Random controls and the no-blackout and plateau reads are reported, not counted.

## Caveats
- **Check-informed.** The candidate reuses WB4 / ST7 / ULT-23 parameters whose check numbers were already seen. That is how E and M come out positive on check at all: they are known edges.
- **Biases that favour the result:**
  - today's symbol list (survivorship, which flatters longs);
  - point-in-time ADV only;
  - no borrow fee, which is correct for a long-only setup.
  Signal minus random (+0.103 check) is the survivorship-neutral read.
- **The live earnings blackout already applies account-wide.** The module relies on it, so it does not re-implement it.
- **Live use needs three YAML entries.** Leg E needs `symbols: module` (WB4 list, min_adv 95M). Legs M and D need STOCKS with min_adv $500M.
- **Rule-change context:**
  - Both halves are scored with one fixed rule set (LR8 costs, the round-4 chassis), so no live ledger change falls inside them.
  - WB4 went live 2026-11-17 (Testing E), after the check window.

## Next step (optimistic, honest)
- E and M are the stable flow edges. Each is ~+0.11-0.13 out of sample, but together they are ~1.0-1.2/session.
- The volume step tried here (WB4-A on large caps) does not carry the edge.
- A next try at volume would need a different "flow" source that keeps the mega-cap / basket property. Two examples:
  - the M collapse on more index-weight names with the RMAX-35 window, which on check gives 32g at 1.98/session, +0.086 (not selectable here);
  - a cross-sectional basket-dislocation trigger.
  Either would need a fresh fit-only pre-registration.

Files:
- `round4/ULT-32/bt.py`, `test_module.py`
- `fitsel.json`, `fit_grid.json`, `fit_random.json`, `dissect_fit.json`
- `check_once.json`, `check_plateau.json`, `dissect_check.json`, `check_trades.csv.gz`
- `modules/ULT-32.py`, `modules/ULT-32_symbols.json`

Educational only — not financial advice.
