Educational only — not financial advice

# ULT-16 COST-GEO — round 2 result: **FAIL**

Research only. No setup, exit, config or account change. Nothing committed.

**In plain words:** we took the ULT-01 short trigger and the ULT-03 long trigger, kept only liquid names (ADV20 >= $150M),
widened the risk unit and tried limit entries, to see if lower cost per R could turn round 1's small losses into gains.
It did not. All 8 versions lost money on the fit half. The frozen pick came out flat on the check half (-0.0006R per
trade, 8.8 trades/session). Liquid names removed most of round 1's cost drag, but no edge was left to keep. Limit
entries made things worse: the orders that filled were the worse trades (adverse selection, as archive P7 warned).

## What was tested (PLAN round2 sec. 3 "ULT-16", unchanged)
- Book: ULT-01 short trigger (gap <= -1.5%, 60 <= RSI5 < 90, dist_lod_atr >= 0.5, SPY since 09:50 <= +0.15%, |sma20
  dist| >= 1.5%, 11:00-15:00, ETB only) + ULT-03 long trigger (RSI14 crossed below 50 in the last 3 bars and <= 30,
  fromOpen <= -1%, buyPressure > 0, not (spy_fo in -0.75..-0.30% and SPY 30-min < 0), 10:15-15:00). Intake: price >= $10,
  |gap| < 20%, ADV20 >= $150M (stocks and ETFs, incl. leveraged), cost_r <= 0.10 (cost_r on the chassis unit u = 0.25 dATR,
  so every config sees one universe).
- Exit: Ru = m x atr_d, bracket +1 Ru limit / -1 Ru stop around the decision close, max hold 45 min, flat 15:50. R is per
  Ru. The R in 0.25-dATR units ("R_u") is shown too.
- MKT entry: open of the next 1-minute bar, LR8 entry cost. LMT entry: limit 0.1u better than the decision close, working
  10 min, filled only in a minute that trades through it by >= $0.01, fill at the limit, entry cost 0, unfilled = no
  trade. In the fill minute only the stop is checked (costlier choice).
- Costs: LR8 + 1.2 bp borrow fee on every short. One lot per symbol, refire >= 30 min after exit, max 2 per
  symbol-session, day cap 30. Shorts not ETB were excluded (466 bars on fit, 943 on check).
- Grid (8): m {0.5, 1.0} x entry {MKT, LMT} x vol floor {none, atr_d% >= 2.5}.

## FIT grid (170 sessions; 2024-10 + 2025-03..09). All 8 configs >= 2/session, all negative

| cfg | label | trades/sess | avg R (per Ru) | avg R_u | avg R w/o best day | total R | total R w/o best day | fill rate | long avg R (n) | short avg R (n) | ex 04-03..04-09 | t (day) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 16a | m0.5 MKT no vol | 7.86 | -0.0402 | -0.0804 | -0.0581 | -53.7 | -75.9 | – | -0.021 (996) | -0.095 (340) | -0.033 | -1.43 |
| 16b | m0.5 MKT vol2.5 | 6.79 | -0.0436 | -0.0871 | -0.0579 | -50.3 | -65.4 | – | -0.017 (818) | -0.108 (336) | -0.029 | -1.56 |
| 16c | m0.5 LMT no vol | 5.18 | -0.0685 | -0.1371 | -0.0829 | -60.3 | -71.6 | 0.480 | -0.047 (590) | -0.112 (290) | -0.054 | -2.21 |
| 16d | m0.5 LMT vol2.5 | 4.49 | -0.0730 | -0.1460 | -0.0855 | -55.7 | -64.2 | 0.466 | -0.043 (477) | -0.123 (286) | -0.054 | -2.25 |
| 16e | m1 MKT no vol | 7.86 | -0.0216 | -0.0864 | -0.0289 | -28.9 | -37.8 | – | -0.013 (996) | -0.046 (340) | -0.017 | -1.65 |
| 16f | m1 MKT vol2.5 | 6.79 | -0.0222 | -0.0889 | -0.0278 | -25.6 | -31.4 | – | -0.011 (818) | -0.050 (336) | -0.014 | -1.68 |
| 16g | m1 LMT no vol | 5.17 | -0.0341 | -0.1363 | -0.0398 | -29.9 | -34.4 | 0.482 | -0.025 (590) | -0.053 (289) | -0.026 | -2.30 |
| **16h** | **m1 LMT vol2.5** | 4.48 | -0.0360 | -0.1439 | -0.0408 | -27.4 | **-30.6** | 0.468 | -0.022 (477) | -0.059 (285) | -0.026 | -2.32 |

The best fit day is 2025-04-07 for every config. **Pick (pre-registered rule: highest fit total R minus the best fit day
among configs >= 2/session) = 16h**, frozen in fitsel.json at 2026-11-19T07:08:43Z, before any check data was built.
The module constants were then set to the pick (M 1.0, ENTRY LMT, VOL_FLOOR 2.5) and their sha256 was added to fitsel.json,
still before any check data.
- **Unit caveat on the pick:** the rule compares totals in R per Ru. At m = 1.0 an R is twice as large as at m = 0.5, so
  the same loss in dollars looks half as big. The rule therefore favours m = 1.0 by construction. In 0.25-dATR units the
  best fit config is 16a (-0.080), and the pick 16h is the second worst (-0.144). This does not matter for the tier:
  every config is negative on fit.

Fit pick 16h in detail: win 0.47, worst day -8.9R (2025-04-07 is the best day, +3.2R), worst day / trade-session -1.78,
SPY up / flat / down -0.010 / -0.006 / -0.064, sub-halves A -0.053 / B -0.010, median hold 45 min, exits: 750 time, 10
stop, 2 target. The 30/day cap removed 270 April crash-day fills (uncapped: 1,033 trades, -0.0135; diagnostic only).

## CHECK — scored once (276 sessions, 2025-10-01..2026-11-04), pick 16h

| metric | value |
|---|---|
| trades / session | 2,416 / 276 = **8.75** (270 sessions traded) |
| LMT fill rate | 0.615 (3,927 orders) |
| win | 0.516 |
| **avg R (per Ru = 1 dATR)** | **-0.0006** (R_u: -0.0026) |
| **avg R w/o best day** | **-0.0023** (best day 2025-11-21, +3.9R; best-day share n/a, total < 0) |
| total R / R per session | -1.55 / -0.0056 |
| worst day; worst day / trade-session | -4.85R (2026-05-19); -0.542 |
| day-clustered t | **-0.10** (bar 3.65 at N = 774) |
| SPY up / flat / down avg R | -0.003 / +0.009 / -0.011 |
| first / second half | -0.003 / +0.002 |
| without 2025-04-03..04-09 | same (no check trades in that window); fit pick without it: -0.026 |
| long | 1,588 trades (5.75/sess), -0.0009, w/o best day -0.0024, t -0.13; SPY down -0.032 |
| short | 828 trades (3.0/sess), -0.0001, w/o best day -0.0030, t -0.01; SPY up -0.042 / down +0.020 |
| exits | 2,409 time, 5 stop, 2 target; median hold 45 min |
| uncapped (diag) | 2,482 trades, -0.0023 |
| bias diagnostic (no borrow; LMT has no signal-close fill to undo) | -0.0000 (fit -0.0353) |

**Random-entry control** (same symbol-sessions, sides and count; random bar in the side's window; same LMT entry and
exit): check random -0.0311 (fill rate 0.671) → signal minus random **+0.024** (long +0.020, short +0.031). Fit: random
-0.0507 (fill 0.705), signal minus random +0.0075 (long +0.017, short -0.008).

## Tier: **FAIL**
- Fit avg R -0.036 < 0. This fails TIER A and TIER B whatever check shows.
- Check avg R -0.0006 ≤ 0 and w/o best day -0.0023 ≤ 0. Volume (8.75/session) is the only bar it clears.
- BEATS: no. t -0.10 against the 3.65 bar, and avg R is about 0.084 below the benchmark's +0.0836.

## Plateau (all 8 configs on check, after the single score; never used to re-select)
All 8 sit between -0.0026 and +0.0015R (R_u -0.0064..+0.0030), |t| <= 0.26. The 3 configs with total R ≥ 0 (16a +0.16,
16b +5.4, 16f +0.2) are all carried by their best day (shares 35.6, 1.07, 15.8, i.e. above 100%: w/o best day all are
negative). Shorts are slightly positive on check in 7 of 8 configs (+0.003..+0.010), longs negative in all 8. That is a
flat book, not a plateau.

## What we learned (for the next round)
1. **The pre-registered caveat holds.** At m = 1.0 the ±1 dATR bracket is hit in under 2% of trades (fit 12/762, check
   7/2,416), so it is a pure 45-min time exit and the R unit is cosmetic. Per 0.25-dATR unit, m = 1.0 is no better than
   m = 0.5 (fit MKT -0.086 vs -0.080). Wider R does not change the edge/cost ratio.
2. **Limit entries carry adverse selection, and we measured it.** LMT costs 0.05-0.06 R_u more per trade than MKT on fit
   (16a -0.080 → 16c -0.137; 16f -0.089 → 16h -0.144), even with no entry cost. Signal bars fill less often than random
   bars (fit 0.47 vs 0.71). The trades that run away in our favour never fill. Do not use passive entries on these triggers.
3. **Liquid names work as a cost fix, not as an edge.** Round 1's ULT-01/ULT-03 check results (-0.003 / -0.006 at R_u)
   go to about 0 here (-0.003..+0.003 R_u). The triggers still beat random entries on the same names on check (+0.024),
   but the base sits at -0.03, so the result is about zero. This agrees with round 1: a good trigger on a losing base
   only shrinks the loss (D3).
4. Fit losses are concentrated in the shorts on SPY-down sessions of 2025-03..05 (sub-half A -0.053 vs B -0.010).

## Live-readiness note
modules/ULT-16.py (two sides in one file, side taken from the setup name; GEOM "S" with stop_price / target_price = ±M x
dATR) passes its smoke test under the live LabStrategy (round2/ULT-16/test_module.py: 3 passed). **The LMT entry of the
pick cannot be expressed by the live LabStrategy / Signal** (entry_type is market or stop only). Run as is, the module
would trade the MKT variant 16f. It is a build for the record, not for deployment.

## Configurations
8 grid + 1 bias diagnostic = **9** (as PLAN sec. 4). Cumulative N for the job = 774 (PLAN round 2 total). Random-entry
controls are reported, not counted.

## Look-ahead / locked-block review
Features are computed from 5-min bars closed at the decision bar plus prior-day atr_d/adv20 (point-in-time test in the
smoke test: the features and triggers at bar i are identical on truncated frames). Outcome columns (win_*, r_long*,
r_short*) and *heat columns are dropped before features are built, with an assert. The locked block is excluded by
month list, pyarrow filters on every 1-minute load and no_locked() asserts. MCF_HIST_ALLOW_LOCKED is refused.
Remaining biases favour the candidate: today's symbol list (longs), today's ETB flag, and a borrow fee of 1.2 bp that may
be low for hard names (those are excluded).

## Rule-change context (owner 2026-11-02)
Both 2-year halves are scored with one fixed rule set (today's), so no live rule change falls inside these results. The
live evidence cited in the PLAN (stop-width and ADV splits) spans the ledger changes listed in round-1 RESULTS.md
(notably 10-30 Testing cost filter, 11-12 LR8 cost model, 11-17 TSZ1 half-size lots / SPYEXIT).

## Files
research/ultimate_1119/round2/ULT-16/: bt.py, fit_grid.json, fitsel.json, fit_random.json, check_once.json,
check_plateau.json, test_module.py; module research/ultimate_1119/modules/ULT-16.py. The work directory (signals and
walked trades) was deleted after scoring and can be rebuilt with bt.py.

Educational only — not financial advice.
