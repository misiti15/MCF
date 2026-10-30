Educational only — not financial advice.

# pdl1030 / structure-exit: structural stops, targets and management on the Failed PDL Break Longs

Plan: PLAN.md (written before scoring). Code: build.py (entry + path cache, TRAIN+VALID only; HOLD months and the locked
block never loaded, 2026-09 cut at 09-15), score.py (sim2 = top5_1028 sim generalised to per-trade stop/target prices,
same costs). Output: score_out.txt, results.csv.

**Configurations scored: 18** (2 parity + 16 variants, all counted). Bar: N = 121459 + 3 x 18 = 121513 -> t >= 4.355.
**Parity passes**: p05 TRAIN -0.0677 / VALID -0.0675 (swarm15 -0.0677 / -0.0675), p10 TV -0.0880 (-0.0880).

**Result: nothing passes. No row has avg R > 0 on TRAIN or VALID.** Entries are unchanged, so every row keeps 100% of the
parent exposure (p05 153.2/session, p10 85.7/session).

| id | rule (p05 entry unless noted) | TRAIN | VALID | t TV | WF% | up-day R | down-day R |
|---|---|---|---|---|---|---|---|
| P05 | parent | -0.0677 | -0.0675 | -9.51 | 5.9 | -0.009 | -0.124 |
| A1 | stop LOD-0.02A | -0.0948 | -0.0903 | -11.86 | 5.9 | -0.028 | -0.155 |
| A2 | stop LOD-0.10A | -0.0581 | -0.0575 | -8.78 | 11.8 | -0.002 | -0.111 |
| A3 | stop LOD-0.25A (STOP*) | -0.0361 | -0.0344 | -6.73 | 11.8 | +0.011 | -0.080 |
| A4 | stop min(LOD-0.05A, e-0.25A) | -0.0555 | -0.0553 | -8.48 | 11.8 | -0.001 | -0.108 |
| A5 | A3 + exit on a close below LOD | -0.0365 | -0.0343 | -9.27 | 5.9 | -0.004 | -0.066 |
| B1-B6 | A3 stop + VWAP / open / prior close / PDL+1x,2x depth / 1:1 target | -0.048..-0.059 | -0.050..-0.065 | -3.5..-5.1 | 12-18 | +0.04..+0.11 | -0.14..-0.22 |
| C1, C2 | BE +0.5R / stop to PDL after +0.25R | = A3 (no-ops: the parent scale-out already moves the stop to entry first) | | | | | |
| C3 | A3 + hard 60-min time stop | -0.0363 | -0.0328 | -8.21 | 11.8 | -0.003 | -0.065 |
| C4 | A3 + half at parent target, runner | -0.0455 | -0.0499 | -5.90 | 11.8 | +0.027 | -0.118 |
| D1 | A3 on the p10 entry | -0.0300 | -0.0317 | -5.43 | 11.8 | +0.010 | -0.071 |

## What was learned
- A stop at the break low (A1) is worse than the parent (-0.095). The low is re-broken on most trades, and the tighter R
  raises cost/R. The "failed failure" is not a clean stop level.
- Wider structural stops help only as much as they widen R. A3 (median 0.46A) is at -0.036, while swarm15's plain
  ATR x3 (0.75A) was at -0.020. Structure adds nothing beyond the width, i.e. beyond the cost-per-R reduction.
- Structural targets (VWAP, open, prior close, measured move, 1:1) raise up-day R to +0.04..+0.11 but deepen down-day R
  to -0.14..-0.22. They lengthen the hold and add market beta. Net avg R gets worse.
- The close-below-LOD exit (A5) and the 60-min time stop (C3) cut the down-day loss (-0.066 / -0.065) but give back the
  same on up days. Avg R is unchanged.
- Exits cannot fix this entry. Gross edge is about 0, and the loss is SPY beta on down sessions. That needs a hedge or a
  tape condition (other families), combined with a wide R (cost per R).
