# pdl1030 / failed-reclaim-short: results (no pass)

*Educational only — not financial advice.*

17 configurations, all pre-declared in PLAN.md, all scored (none added after the fact). Bar: N = 121512 + 3 x 17 = 121563,
t_day >= 4.355. TRAIN+VALID only (348 sessions); HOLD months and the locked block were never loaded.
Scripts: score_frs.py (uses se_score.py, a verbatim copy of pdl1030/structure-exit/score.py, on the structure-exit cache);
output score_out.txt, results.csv.

## Parity (passes)
- Parents via structure-exit sim2: p05 TRAIN -0.0677 / VALID -0.0675 (n 53,326), p10 TV -0.0880 (n 29,836): diff 0.0000.
- Short simulator: row A1 equals the pdl1030/tape-flip `Sb` leg (top5_1028 sim, side -1) on all 41,338 trades, row by
  row (100% identical r, TV mean -0.0643).

## Results (avg R after costs; up/down = SPY session sign)
| id | rule | /sess | TRAIN | VALID | t | WF% | up / down |
|---|---|---|---|---|---|---|---|
| A1 | short 1st close < PDL, stop 0.25A, parent-mirror exits | 118.8 | -0.0745 | -0.0470 | -9.1 | 0 | -0.130 / -0.010 |
| A2 | short 1st close < signal LOD, stop 0.25A | 64.3 | -0.0722 | -0.0449 | -8.1 | 0 | -0.120 / -0.027 |
| A3 | close < PDL, stop reclaim high + 0.02A | 118.8 | -0.1015 | -0.0719 | -13.2 | 0 | -0.144 / -0.046 |
| A4 | close < LOD, stop reclaim high + 0.02A | 64.3 | -0.0596 | -0.0386 | -6.4 | 0 | -0.123 / -0.009 |
| A5 | close < LOD, stop 0.75A | 64.3 | -0.0305 | -0.0152 | -2.8 | 11.8 | -0.113 / +0.028 |
| B1-B4 | A5 + 1R / 2R / no target / BE after 1R | 64.3 | -0.030..-0.034 | -0.030..-0.033 | -1.6..-2.0 | 23-35 | -0.18 / +0.05..+0.06 |
| C1 | B3 + round trip <= 5% of R | 57.3 | -0.0241 | -0.0240 | -1.3 | 35.3 | -0.172 / +0.065 |
| C2 | B3 + SPY below open at trigger | 43.2 | -0.0342 | -0.0305 | -1.4 | 29.4 | -0.351 / +0.039 |
| C3 | B3 + breadth < 0.5 | 47.5 | -0.0329 | -0.0402 | -1.5 | 23.5 | -0.261 / +0.049 |
| C4 | B3 + cost <= 5% + breadth < 0.5 | 42.3 | -0.0283 | -0.0325 | -1.3 | 35.3 | -0.256 / +0.056 |
| C5 | B3 + trigger within 6 bars of the signal | 27.9 | -0.0033 | -0.0481 | -0.8 | 23.5 | -0.209 / +0.101 |
| D1 | C5 on the p10 pool | 12.2 | +0.0058 | -0.0531 | -0.5 | 23.5 | -0.229 / +0.120 |

Selections (TRAIN only): A* = A5, E* = B3, BEST (>= 25/sess) = C5.

## What was learned
- The failed-reclaim short loses about as much as the long on the parent's tight 0.25A stop (-0.045..-0.075). The signal has
  no direction: shorting the failure is the long's mirror with costs paid again.
- Waiting for the deeper failure (close below the signal-bar day low, TL) halves the exposure (64/session) and barely helps
  at 0.25A. A structural stop above the reclaim high is worse on PDL (tighter R, more cost per R) and slightly better on LOD.
- The only real lift is stop width (0.75A: cost per R falls; stops hit 4-6%). That gives about -0.02..-0.03, the same
  plateau as swarm15's x3 stop and the cost floor on the long side.
- Held to the close, the short is a pure market-beta trade: +0.06 on SPY down sessions, -0.18 on up sessions. Tape gates
  known at the trigger (SPY below open, breadth < 0.5) do not pick the down sessions; they make up-session losses worse
  (-0.26..-0.35), because the trigger often comes at the morning low of a reversal day.
- Fast failures (C5) are flat on TRAIN but -0.048 on VALID; not stable. Nothing passes; no module written.

Educational only — not financial advice.
