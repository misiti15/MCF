# PYRAMID round 3 — Team N ("new blood, honest fitness") — pre-registration
Educational only — not financial advice. Research only: no config / setup / account / ledger change.
Written 2026-11-25 BEFORE any rule of this search was scored. Inputs read so far: BRIEF, pyramid_1124 SUMMARY + L1/L2/L3/E/G
reports, top10 BENCHMARK.md + PLAN.md, ex30/gen2 PLAN/NOTES/gen.py, repsrot_1125 REPORT. No candidate R seen.

## Machinery (reused, not new)
- Rule grammar = ex30/gen2 (research/bdi/ex30/gen2/gen.py `prims`: 19 triggers, 35 contexts, 3 geometries t1s1/t05s1/t1s05,
  windows W1 10:00-11:30, W2 11:30-14:00, W3 10:00-15:00 bar close; first qualifying bar per symbol-day; R = 0.25 x ATR_d).
- Draws = the GEN pipeline's way (mcf/research/generator: seeded random draws from the grammar), budget fixed below.
- Finalist scoring = research/ultimate_1119/top10/bench10.py unchanged (signals -> 1-minute exit walk -> add_r LR8 costs
  incl. 1.2 bp short borrow, x3 extended tier -> TESTING_RULES book: cap 100, <=3 lots/symbol, price >= $5, stop-cost filter
  0.15R; shorts ETB >= 0.9 of snapshots, L2/etb_rate.parquet).

## Universe / filters (all candidates)
lab frames (research/history2y, 1,226 symbols), ADV20 >= $95M point-in-time, price >= $5. Breadth contexts (br_*) dropped
(no T2 breadth). Locked block 2024-11-01..2025-02-28 never read (asserts).

## Search space and budget: N = 300 candidates, all counted
- LONGS (240 draws), ALL behind ONE pre-registered market gate G: SPY at or above its open at the decision bar (spy_fo >= 0,
  point-in-time lab context; L2's gate). TT1 is NOT used (one gate only).
  Triggers (15): vwdn hod bulldiv beardiv uwick lwick rsi5dn macdup macddn flowup flowdn wide inside round dry
  (gen2 HARD long exclusions vwup/rsi5up/lod/volsurge removed). Contexts (28): gen2 CTX minus spy_up/spy_dn/spy_flat,
  br_hi/br_lo/br_mid, blw_pdl.
- SHORTS (60 draws), no market gate, easy-to-borrow only, NOT the gap-down family: gap > -1.0% hard filter, no gap_dn context.
  Triggers (14): vwdn lod bulldiv beardiv uwick lwick rsi5dn macdup macddn flowup wide inside round dry
  (gen2 HARD short exclusions vwup/rsi5up/flowdn/hod/volsurge removed). Contexts (30): gen2 CTX minus br_*, gap_dn, abv_pdh.
- Draw: numpy default_rng(20261125). Per rule: trigger uniform; number of contexts k: P(0)=0.15, P(1)=0.45, P(2)=0.40,
  drawn without replacement, redraw if two contexts are from the same family (same prefix before "_", e.g. fo_up+fo_flat;
  vr_lo/vs_hi count as one "volume" family); geometry uniform; window uniform. Duplicates redrawn. 240 unique longs then
  60 unique shorts. Every drawn rule is scored on FIT and counted (N = 300).

## Fitness (FIT only = bench10 fit half: 2024-10 + 2025-03..09, 170 sessions; lab 5-min outcome columns)
Trade R (lab basis) = gates.prod_r (1c + 1 bp per side, target exit free, +2c on stops, time-of-day entry multiplier),
cost part x3 when |gap| >= 20% or price < $5, minus 1.2 bp borrow on shorts.
Eligible only if: trades >= 85 (>= 0.5/session) and <= 25/session; >= 20 trades on SPY-down days (SPY 09:30 open -> close
<= -0.30%, bench10 definition); best-day share of total R < 0.50.
F = min( avg R, avg R without the best day, avg R on SPY-down days ).   (rejects one-day records and down-day losers)

## Selection (FIT only, frozen before any CHECK / T2 read)
Per side, walk by F descending; keep a rule if it is eligible, its trigger differs from every kept rule of that side and its
FIT symbol-day set has Jaccard < 0.30 with every kept rule of that side. Keep 3 longs + 2 shorts. If fewer than 3 longs /
2 shorts have F > 0, the slots are filled by the next eligible rules (flagged "F<=0 filler"); if no eligible rule, slot empty.

## Scoring ONCE (finalists only): FIT, CHECK 2025-10-01..2026-11-04 (276 s), T2 2023-01-03..2024-09-13 (427 s, cache_fresh 469)
bench10 pipeline as above. Card per BRIEF: trades, sessions, /session, avg R (fit/check/T2), win vs break-even, day-clustered t,
w/o best day + share, check halves, SPY up/flat/down, median hold, total R/session, worst day; Primary reference book (L1's saved
prim rows, Primary rules, G method) daily-R correlation + R on its 10 worst days; vs random control.
Random control (fair, same universe, not counted): day-matched mean lab-basis R of EVERY eligible bar that date with the same
side / geometry / window / universe filters (gate G for longs; ETB + gap > -1% for shorts); cand lab-basis R minus that, on FIT,
CHECK, T2.

## Verdict bars (fixed now)
- PASS: check avg R > 0 AND T2 avg R > 0 AND check w/o best day > 0 AND beats random control on CHECK and on T2.
- TIER A (-> Testing suggestion, owner decision): PASS + fit > 0, check day-clustered t >= 1.5, both check halves > 0,
  >= 0.5 trades/session on check, check best-day share < 0.5.
- ULTIMATE (top-10 standard, best top-10 values in top10/BENCHMARK.md): TIER A + check avg R >= +0.071, T2 >= +0.034,
  check w/o best day >= +0.028, check total R/session > 0.
- TIER B: fit > 0 and check > -0.02.  Else FAIL.
Multiple testing: within this search N = 300 -> expected best-of-noise FIT t ~ sqrt(2 ln 300) = 3.38; job cumulative N
~1,917 (+ G's 10) + 300 ~ 2,230 -> 3.93. CHECK is read on 5 rules only (Bonferroni-5 one-sided 5% t ~ 2.33).
