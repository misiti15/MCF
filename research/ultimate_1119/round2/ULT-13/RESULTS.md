Educational only — not financial advice

# ULT-13 ST7-SHARP — ST7's one-bar RSI(14) collapse + a down-tape guard, LONG (round 2)

**Tier: FAIL. Not TIER A, not B, not BEATS.** Every one of the 8 configurations loses on FIT after costs (-0.018 to
-0.099R per trade), so TIER A and TIER B are both out of reach (both need fit avg R > 0). The fit pick **13f** (RMAX 35,
no guard, TX45) was scored once on CHECK: **+0.019R/trade** (without its best day +0.014, day-clustered t 1.58 against a
3.65 bar, 6.46 trades/session, +34.7R over 276 sessions). That is positive but weak and well below the benchmark
(+0.0836 / +0.0734). **The down-tape guard G1, the targeted remedy, made every config worse in both halves.**

## In plain words
- We kept ST7's real trigger: RSI(14) drops from >= 50 to <= 30 (or <= 35) in a single 5-minute bar. The stock must also
  be at least 1% below its open, with 19-bar buy pressure > 0. Then we widened the universe to ADV >= $50M, used the
  whole 09:50-15:00 window, and tested a SPY down-tape guard.
- **The volume came through.** With RSI <= 35 it trades 3.4/session on fit and 6.5/session on check (ST7-FD: 1.5 / 3.1).
- **The guard did not fix the fit losses.** ST7's fit losses sit on SPY-down days, but the end-of-day label can't be seen
  at signal time. The point-in-time guard (SPY <= -0.30% from its open and not rising over 30 min) removed the
  down-day trades that were *less* bad. The down-day trades it kept got worse (13f -0.108 -> 13h -0.197 on fit). It made
  4 of 4 pairs worse on fit (by 0.006-0.012R per trade) and 4 of 4 worse on check (by 0.009-0.035R).
- **Fit is carried by the April 2025 crash week in both directions.** The best fit day is 2025-04-07 (+9.7R) and the worst
  is in the same week (-21.4R). Without 2025-04-03..04-09, the pick's fit avg R is -0.002, about flat. So the base fit
  record is "flat, plus a crash-week loss". It is not a strong negative, but it is not positive either.
- **Check is positive but weak.** +0.019R (t 1.58). First half -0.004, second half +0.035, so most of the check result
  comes late. The trigger does beat random entries in the same names: check random -0.058 (signal +0.077 better), fit
  random -0.053 (signal +0.030 better). As in round 1, the trigger adds value, but the base it sits on loses about
  0.05R to costs and drift.
- The configuration closest to ST7-FD itself (13a: RMAX 30, t1s1) is +0.071 on check (2.18/session, t 1.85). But it is
  -0.088 on fit at 0.95/session, so it is not eligible and not a candidate. It is reported only as a plateau read.

## Build (faithful to round2/PLAN.md sec. 3 "ULT-13")
- Live module `research/ultimate_1119/modules/ULT-13.py`: `SIDE`, `GEOM`, `LAYERS`, `features()`, `trigger()`, `mask()`,
  `stop_price()` (GEOM "S" for TX45). Constants are set to the fit pick (RMAX 35, G0, EXIT "X"). bt.py imports
  `features()` / `trigger()`, so the backtest and live share one code path. YAML it would need (NOT written to any config):
  `type: lab, module: research/ultimate_1119/modules/ULT-13.py, min_adv: 50000000, window: [950, 1500],
  context: [spy_fo], refire: true, refire_cooldown: 0, geom: S, time_stop_min: 45, time_stop_min_r: 99`.
- Smoke test `round2/ULT-13/test_module.py` (3 passed). It covers:
  - fires under the live LabStrategy on a one-bar collapse;
  - t1s1 gives +-1u; geom S gives a 2u stop with no target;
  - a 25-minute slide does not fire (one-bar only);
  - G1 blocks a SPY -0.95%-and-falling day that G0 trades;
  - the universal SPY long filter blocks;
  - no SPY context gives no signal;
  - features do not change when later bars are removed (no look-ahead).
- Build rules fixed before any fit scoring:
  - RSI14[prev] is the same symbol-session's bar exactly 5 min earlier. The frames start at 09:50, so the first
    possible signal is 09:55.
  - G1: when spy_r30 is unknown (before the 10:20 bar), the guard decides on spy_fo alone.
  - The universal long filter applies in G0 and G1. It removed 140 fit / 337 check superset bars.
- Chassis:
  - Intake: U2 (price >= $10, |gap| < 20%, atr_d > 0, cost_r <= 0.10, point-in-time ADV20 >= $50M).
  - Entry: the OPEN of the 1-minute bar that starts at the decision close.
  - t1s1 cap45 = +-1u around the decision close (u = 0.25 dATR), R per u. TX45 = 2u catastrophic stop with a 45-min
    time exit, R per 2u (actual risk); the 0.25-dATR figure is 2x.
  - Exits walked on 1-minute bars as bench.py (stop first, gap-through at the worse of open/stop, target with no
    exit cost, flat 15:50). LR8 costs.
  - Long only, so no borrow fee.
  - One lot per symbol, refire >= 30 min after the exit, max 2 per symbol-session, day cap 30. The cap never bound
    materially: check uncapped 1,790 vs capped 1,782.
- Forbidden frame columns (win_*, r_long*, r_short*, any *heat*) are dropped before features are built. Locked block
  never read: pyarrow filters on frame and 1-minute loads, `no_locked()` asserts, MCF_HIST_ALLOW_LOCKED refused.
- Survivorship: 1,226 lab symbols (today's list) flatters longs. The signal-minus-random figure is the
  survivorship-neutral read.

## Selection (FIT only) — every configuration
Rank = fit total R minus the best fit day, among configs with >= 2.0 trades/session (eligible: 13e, 13f, 13g, 13h).
Best fit day is 2025-04-07 for every config. Best-day share is n/a everywhere (total R < 0).

| cfg | RMAX-guard-exit | FIT /sess | FIT avg R | (0.25 dATR) | w/o best day | total R | total w/o best | worst day / trade-sess | t | SPY up / flat / down | ex 04-03..09 | A / B | CHECK plateau (after the single score): avg R / w/o best / t / per sess |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 13a | 30-G0-t1s1 | 0.95 | -0.088 | -0.088 | -0.116 | -14.1 | -18.3 | -9.45 | -0.72 | +0.272 / -0.097 / -0.338 | +0.004 | -0.228 / +0.099 | +0.071 / +0.055 / 1.85 / 2.18 |
| 13b | 30-G0-TX45 | 0.95 | -0.072 | -0.144 | -0.086 | -11.6 | -13.4 | -6.26 | -0.93 | +0.098 / -0.053 / -0.209 | -0.007 | -0.137 / +0.015 | +0.037 / +0.027 / 1.81 / 2.18 |
| 13c | 30-G1-t1s1 | 0.86 | -0.099 | -0.099 | -0.131 | -14.5 | -18.6 | -9.77 | -0.75 | +0.272 / -0.097 / -0.450 | +0.001 | -0.245 / +0.073 | +0.036 / +0.027 / 1.02 / 2.00 |
| 13d | 30-G1-TX45 | 0.86 | -0.082 | -0.165 | -0.098 | -12.0 | -13.9 | -6.48 | -0.99 | +0.098 / -0.053 / -0.284 | -0.012 | -0.151 / -0.002 | +0.024 / +0.019 / 1.26 / 2.00 |
| 13e | 35-G0-t1s1 | 3.36 | -0.018 | -0.018 | -0.061 | -10.2 | -33.2 | -8.15 | -0.24 | +0.193 / -0.038 / -0.168 | -0.001 | -0.050 / +0.026 | +0.033 / +0.024 / 1.54 / 6.46 |
| **13f** | 35-G0-TX45 | 3.36 | -0.022 | -0.045 | -0.041 | -12.8 | **-22.5** | -5.62 | -0.51 | +0.071 / -0.009 / -0.108 | -0.002 | -0.054 / +0.021 | **+0.019 / +0.014 / 1.58 / 6.46** |
| 13g | 35-G1-t1s1 | 2.85 | -0.029 | -0.029 | -0.081 | -14.2 | -37.1 | -9.23 | -0.35 | +0.193 / -0.038 / -0.306 | -0.015 | -0.076 / +0.022 | +0.013 / +0.008 / 0.65 / 5.90 |
| 13h | 35-G1-TX45 | 2.85 | -0.032 | -0.064 | -0.055 | -15.4 | -25.1 | -6.36 | -0.63 | +0.071 / -0.009 / -0.197 | -0.009 | -0.074 / +0.015 | +0.011 / +0.008 / 0.96 / 5.90 |

**Remedy effect report (G1 vs G0, same RMAX/exit), as CLAUDE.md "Remedies" asks:**

| pair | fit avg R, G0 -> G1 | check avg R, G0 -> G1 |
|---|---|---|
| 13a -> 13c | -0.088 -> -0.099 | +0.071 -> +0.036 |
| 13b -> 13d | -0.072 -> -0.082 | +0.037 -> +0.024 |
| 13e -> 13g | -0.018 -> -0.029 | +0.033 -> +0.013 |
| 13f -> 13h | -0.022 -> -0.032 | +0.019 -> +0.011 |

- 0 of 4 pairs improve, 4 of 4 get worse in both halves.
- The guard removes 15-87 fit trades, almost all on days that end SPY-down (84 of 87 for RMAX 35; the rest on flat days). The removed trades were less bad than the down-day
  trades that remain, so SPY-down avg R falls (for example 13e: -0.168 -> -0.306).
- **Point-in-time tape state does not find ST7's bad days.** The losing days are ones where SPY falls *after* the
  signal.

## The fit pick 13f, fit vs check (R per actual risk = 2u; the 0.25-dATR figure is shown in brackets)

| | FIT (170 sess) | CHECK (276 sess, scored once) |
|---|---|---|
| trades (/session) | 571 (3.36) | 1,782 (6.46) |
| win | 0.482 | 0.532 |
| avg R | -0.022 (-0.045) | **+0.019 (+0.039)** |
| avg R w/o best day | -0.041 | **+0.014** |
| best day (share) | 2025-04-07 +9.7R (n/a, total < 0) | 2026-06-17 +10.1R (0.29, no 1-day tag) |
| total R / R per session | -12.8 / -0.075 | +34.7 / +0.126 |
| worst day / per trade-session | -21.4 / -5.62 | -5.5 / -0.82 |
| day-clustered t | -0.51 | **1.58** (bar 3.65) |
| SPY up / flat / down avg R | +0.071 / -0.009 / -0.108 | +0.037 / +0.017 / +0.004 |
| without 2025-04-03..04-09 | -0.002 | +0.019 (window outside check) |
| sub-halves / check halves | A -0.054 / B +0.021 | first -0.004 / second +0.035 |
| same-name random entry (signal - random) | -0.053 (+0.030) | -0.058 (+0.077) |
| bias diagnostic: signal-close fill (no borrow: long) | -0.017 (next-minute fill costs 0.006R) | +0.023 (0.004R) |
| exits | 553 time / 18 stop | 1,750 time / 32 stop |
| median hold | 45 min | 45 min |

## Bars
- TIER A: check avg R > 0 yes (+0.019); w/o best day > 0 yes (+0.014); **fit avg R > 0 NO (-0.022)**; >= 2/session yes
  (6.46); no look-ahead yes. **Not TIER A.**
- TIER B (fit > 0 and check > -0.02): **no** (fit < 0). -> **FAIL.**
- BEATS: no. Check +0.019 is below +0.0836, w/o best day +0.014 is below +0.0734, and t 1.58 is below 3.65.
  Total R/session > 0 and worst day/trade-session -0.82 >= -2.152 do pass.

## What can be salvaged (for the next round, not a re-selection)
- The one-bar trigger beats same-name random entries in both halves (+0.030 fit, +0.077 check). The trigger information
  is real. The problem is the base: random entries in these names over 45 minutes lose about 0.05R after costs.
- A tape remedy needs a *forward-looking* read of the tape (for example breadth deterioration or a QQQ VWAP loss
  *before* the signal), or a base that is >= 0 on its own (D3). Removing "SPY already down" bars removes the wrong
  trades.
- 13a's check +0.071 at 2.2/session is ST7-FD-like. The benchmark ST7-FD (ADV $95M) stays the better version of this
  idea. Widening to ADV $50M / RMAX 35 adds volume without adding edge.

## Configurations and context
- Configurations: 8 grid + 1 bias diagnostic = 9 for ULT-13, all already in the round-2 count (PLAN sec. 4).
  Cumulative N = 774, so the t bar is 3.65. The random-entry controls are reported and not counted.
- Rule-change context: both 2-year halves are scored with one fixed rule set (today's LR8 costs, round-2 chassis). No
  live ledger change falls inside them. No live figures are quoted here.
- Files: `round2/ULT-13/{bt.py, test_module.py, fit_grid.json, fitsel.json (frozen 2026-11-19 before any check data;
  sha256 of bt.py and module), check_once.json, check_plateau.json, fit_random.json}`. Trade lists were kept in the
  scratchpad only and deleted after scoring.

Educational only — not financial advice.
