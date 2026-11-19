Educational only — not financial advice

# ULT-12 ETF-DIP-X — NM-ETF WB4's own trigger on new universes / windows, LONG (round 2)

**Tier: B (near miss, never deployed). Not TIER A, not BEATS.** The fit pick 12a (all ETFs/ETNs with ADV >= $50M,
WB4's % trigger, 14:00-15:00) scored **-0.005R/trade on check** (w/o best day -0.014, t = -0.21, 4.2 trades/session,
total -5.4R over 276 sessions). On fit it was +0.107 (w/o best day +0.087, t 3.01). Fit avg R > 0 and check > -0.02
make it TIER B.

## In plain words
- We kept NM-ETF WB4's trigger exactly as it is: a sharp 15-min drop (<= -0.75%), +DI(7) - -DI(7) >= -5, a 60-min
  return >= -1.0% (falling-hour guard) and daily ATR >= 3.6%. Then we tried it on wider sets of names (all ETFs, liquid
  stocks) and a longer window (13:00-15:00), one change at a time.
- **On stocks it does not work.** Every stock version with the % trigger was flat to negative on fit and negative on
  check (-0.026 to -0.036R). The ATR-scaled stock versions trade too rarely (0.7-2.3/session) and their check results
  depend on one or two days.
- **Widening from WB4's ETF list to every ETF is what broke it.** On fit, 12a looked good (+0.107R, 3.4/session). On
  check, the WB4-list ETFs inside 12a still earned **+0.098R** (240 trades). The extra ETFs lost **-0.032R** (919
  trades, 3.3/session): mostly single-stock 2x funds (MSTX, SNXX, SNDU, MULL, MUU, AAOX) that were rare or absent on fit.
  They swamped the good part.
- **The original edge held up.** The anchor diagnostic (exact WB4 list, ADV >= $95M, same chassis with a next-minute
  fill) was **+0.110R on check, w/o best day +0.096, t 2.87**. But it traded only 0.82/session (fit 1.41), so it cannot
  reach TIER A's 2/session floor. Read it only as confirmation of NM-ETF/WB4; it was not selected (the anchor was not
  eligible for selection).
- Random entries on the same ETF-sessions: fit -0.000 (signal +0.107 better), check -0.018 (signal +0.013 better).
  So the trigger still picks better entries than random on check, but only by a little.

## Build (faithful to round2/PLAN.md sec. 3 "ULT-12")
- Live module `research/ultimate_1119/modules/ULT-12.py` + `ULT-12_symbols.json` (universes frozen before any fit
  scoring). `features()` / `trigger()` call `mcf.research.arena.indicators.compute` (the same call WB4 makes). bt.py
  imports them, so the backtest and live share one code path. Smoke test `round2/ULT-12/test_module.py` (2 passed): the
  module fires under the live LabStrategy (`context: [spy_fo]`, `symbols: module`), gives t05s1 levels, rejects a
  non-member symbol, applies the universal SPY long filter, fails safe without SPY context, and its features do not
  change when later bars are removed (no look-ahead).
- Universes: E = 205 ETF/ETN/fund names in the 1,226-name lab list (universe.csv name match + the WB4 list + SPY;
  false matches such as REITs, SCHW and PATH removed by hand), ADV >= $50M; S200 / S100 = the other 1,021 lab names,
  ADV >= $200M / $100M. Point-in-time ADV20.
- Build interpretation (fixed before fit): the ATR-scaled variant keeps WB4's atr_d_pct >= 3.6 floor. Only the drop
  and the guard scale with ATR.
- Chassis: U2 intake (price >= $10, |gap| < 20%, cost_r <= 0.10); universal long filter (no long while SPY is -0.30..
  -0.75% from its open and falling over 30 min). It removed 491 fit / 1,603 check superset bars. Entry = OPEN of the
  1-minute bar starting at the decision close. t05s1 bracket around the decision close (u = 0.25 dATR, as live), 45-min
  cap, flat 15:50. LR8 costs. Long only, so no borrow fee. One lot per symbol, refire >= 30 min after the exit, max
  2/symbol-session, day cap 30 (never bound: capped = uncapped on check). The live module's refire (2nd hit >= 6 bars
  after the 1st, max 2) is a little looser than the backtest's exit-based chain. Noted, not modelled.
- Forbidden frame columns (win_*, r_long*, r_short*, any *heat*) are dropped before features are built.
- Locked block: never read (pyarrow filters on frames / 1-min loads, `no_locked()` asserts, MCF_HIST_ALLOW_LOCKED
  refused).

## Selection (FIT only) — every configuration
Rank = fit total R minus best fit day, among configs with >= 2.0 trades/session (eligible: 12a, 12b, 12e, 12f, 12i, 12j).

| cfg | universe-drop-window | FIT /sess | FIT avg R | w/o best day | best-day share | total R | total w/o best | t | CHECK (plateau, after the single score) avg R / w/o best / t / per sess |
|---|---|---|---|---|---|---|---|---|---|
| **12a** | E-pct-1400 | 3.44 | +0.107 | +0.087 | 0.23 | +62.5 | **+48.1** | 3.01 | **-0.005 / -0.014 / -0.21 / 4.20** |
| 12b | E-pct-1300 | 6.05 | +0.060 | +0.046 | 0.26 | +61.6 | +45.5 | 2.02 | -0.027 / -0.032 / -1.56 / 8.00 |
| 12c | E-atr-1400 | 0.61 | +0.175 | +0.121 | 0.43 | +18.2 | +10.3 | 2.48 | +0.131 / +0.102 / 1.71 / 0.29 |
| 12d | E-atr-1300 | 0.90 | +0.170 | +0.080 | 0.62 **1 day** | +26.0 | +9.8 | 1.84 | +0.002 / -0.019 / 0.02 / 0.54 |
| 12e | S200-pct-1400 | 4.22 | +0.006 | -0.016 | 3.71 **1 day** | +4.0 | -10.7 | 0.11 | -0.036 / -0.042 / -1.51 / 7.67 |
| 12f | S200-pct-1300 | 7.35 | +0.040 | +0.029 | 0.30 | +50.4 | +35.4 | 1.38 | -0.026 / -0.030 / -1.48 / 13.84 |
| 12g | S200-atr-1400 | 1.19 | +0.053 | -0.013 | 1.21 **1 day** | +10.8 | -2.2 | 0.46 | +0.024 / -0.025 / 0.36 / 0.72 |
| 12h | S200-atr-1300 | 1.55 | +0.071 | +0.014 | 0.83 **1 day** | +18.7 | +3.2 | 0.78 | +0.057 / +0.034 / 1.32 / 1.41 |
| 12i | S100-pct-1400 | 5.40 | -0.012 | -0.029 | n/a | -11.4 | -25.9 | -0.29 | -0.036 / -0.041 / -1.75 / 9.98 |
| 12j | S100-pct-1300 | 9.49 | +0.029 | +0.020 | 0.32 | +46.6 | +31.6 | 1.10 | -0.029 / -0.032 / -1.91 / 17.37 |
| 12k | S100-atr-1400 | 1.45 | +0.020 | -0.040 | 2.73 **1 day** | +5.0 | -8.7 | 0.19 | -0.001 / -0.043 / -0.02 / 1.16 |
| 12l | S100-atr-1300 | 1.92 | +0.034 | -0.015 | 1.41 **1 day** | +11.0 | -4.5 | 0.42 | +0.022 / +0.004 / 0.60 / 2.29 |
| anchor | WB4 list-pct-1400, ADV $95M | 1.41 | +0.219 | +0.178 | 0.29 | +52.3 | +37.2 | 4.14 | +0.110 / +0.096 / 2.87 / 0.82 |

Plateau: every eligible (>= 2/session) config is negative on check. The configs that are positive on check all trade
< 1.5/session (except 12l, +0.022 with 82% of its check total from one day). Fit sub-halves of 12a: A +0.140 / B +0.022,
already fading inside fit.

## The fit pick, fit vs check (R per u = 0.25 dATR; actual risk ~ u, so the 0.25-dATR figures are the same)

| | FIT (170 sess) | CHECK (276 sess) |
|---|---|---|
| trades (/session) | 584 (3.44) | 1,159 (4.20) |
| win | 0.651 | 0.515 |
| avg R | +0.107 | **-0.005** |
| avg R w/o best day | +0.087 | -0.014 |
| best day (share) | 2025-04-10 +14.4R (23%) | 2026-07-29 +10.1R (n/a, total < 0) |
| total R / per session | +62.5 / +0.368 | -5.4 / -0.020 |
| worst day / per trade-session | -3.93 / -0.92 | -5.86 / -1.23 |
| day-clustered t | 3.01 | -0.21 (BEATS floor 3.65 at N = 774) |
| SPY up / flat / down avg R | +0.099 / +0.064 / +0.140 | +0.027 / -0.037 / -0.001 |
| avg R without 2025-04-03..04-09 | +0.078 | -0.005 (no April 2025 in check) |
| first / second half | +0.140 / +0.034 | +0.035 / -0.038 |
| exits target / time / stop | 292 / 251 / 41 | 347 / 752 / 60 |
| median hold | 34 min | 45 min |
| same-name random entry avg R (signal - random) | -0.000 (+0.107) | -0.018 (+0.013) |
| bias diagnostic: signal-close fill | +0.111 | -0.002 |
| uncapped (day cap off) | 651 trades, +0.128 | identical to capped |

Inside 12a by family (diagnostic after the check score, `diag_wb4_split.json`): WB4-list ETFs fit +0.205 (1.46/sess),
check +0.098 (0.87/sess); other ETFs fit +0.034 (1.97/sess), check -0.032 (3.33/sess). Worst check names outside the
WB4 list: MSTX -6.4R, SNXX -4.7, SNDU -4.2, MULL -4.0, MUU -3.9, AAOX -3.1 (single-stock 2x funds). Survivorship
(today's list) flatters longs. The signal-minus-random figure is the survivorship-neutral read.

## Bars
- TIER A: check avg R > 0 **no** (-0.005); w/o best day > 0 **no**; fit avg R > 0 yes; >= 2/session on check yes (4.20);
  no look-ahead yes. -> not A.
- TIER B: fit avg R > 0 and check avg R > -0.02 -> **B** (round-1 bar; next round only, never deployed).
- BEATS: no (needs A, avg > +0.0836, w/o best > +0.0734, t >= 3.65).

## What to carry forward (optimistic, honest)
- NM-ETF/WB4's edge is real out of sample on this pipeline (anchor check +0.110, t 2.87). It belongs to index/sector
  (incl. 3x index) ETFs, not to single-stock leveraged funds or stocks. A round-3 version that adds volume WITHOUT
  single-stock leveraged ETFs could work: index/sector/3x-index ETFs at a lower ADV floor, plus the 13:00 window on the
  WB4 list only. Expect ~1-1.5/session at best. That is still short of TIER A's 2/session, so it would need a lower
  floor, or to be pooled with another lane.
- The pure % trigger on liquid stocks is a dead end (all 6 configs negative on check).

## Configurations and files
- This candidate: 12 grid + 1 anchor diagnostic + 1 bias diagnostic (signal-close fill) = 14. All were pre-counted in
  round2/PLAN.md. Cumulative N stays 774 (t floor 3.65). Random controls are reported, not counted.
- fitsel.json frozen 2026-11-19T06:35:54Z, before any check frame was built (`sig check` asserts it exists). The module
  sha at freeze differs from the final one only by a comment line naming the pick (the pick's constants E / pct /
  1400-1500 were already the defaults). The check score was run once (06:40:50Z). The plateau and the family split came
  after.
- Files: `round2/ULT-12/{bt.py, test_module.py, fit_grid.json, fitsel.json, fit_random.json, check_once.json,
  check_plateau.json, diag_wb4_split.json}`, `modules/ULT-12.py`, `modules/ULT-12_symbols.json`. Trade lists were in
  the scratchpad and have been deleted.
- Rule-change context: the 2-year halves use one fixed rule set; no ledger change falls inside them. WB4 itself went
  live 2026-11-17 (Testing E), after the check window ends (2026-11-04).

Educational only — not financial advice.
