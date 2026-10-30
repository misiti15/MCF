# pdl1030 / tape-flip: results (no pass)

*Educational only — not financial advice.*

The 16 configurations are pre-declared in PLAN.md and all 16 were scored. Lineage N = 121459 + 3 x 16 = 121507, which sets the bar at t >= 4.355.
Data is TRAIN+VALID only (348 sessions). HOLD months and the locked block were never loaded. Harness and costs are the same as swarm15 (run.py -> cache/, score.py -> results.csv).

## Parity (passes, diff 0.0000)
- p05: TRAIN -0.0677 / VALID -0.0675, n 53,326 (swarm15 matches).
- p10: TRAIN -0.0861 / VALID -0.0912, n 29,836 (swarm15 matches).

## Results

| id | trades/sess | TRAIN | VALID | t_day | WF% | up / down session |
|---|---|---|---|---|---|---|
| parent p05 | 153.2 | -0.0677 | -0.0675 | -9.51 | 5.9 | +0.014 / -0.146 |
| TA-F SPY fromOpen flip | 152.9 | -0.0593 | -0.0436 | -8.89 | 0 | -0.058 / -0.029 |
| TB-F SPY VWAP flip | 153.2 | -0.0419 | -0.0488 | -8.47 | 11.8 | -0.046 / -0.024 |
| TC-F breadth flip | 153.1 | -0.0392 | -0.0498 | -7.88 | 11.8 | -0.034 / -0.020 |
| TB-B / TC-B re-break flip | 136 | -0.058 | -0.057 / -0.062 | about -10.5 | about 6 | -0.04 / -0.04 |
| gates G (long only when up) | 72-75 | -0.047 to -0.067 | -0.062 to -0.070 | -6.4 to -7.2 | <= 11.8 | about 0 / -0.15 to -0.17 |
| short legs Sx (down tape only) | 78-81 | -0.032 to -0.053 | -0.027 to -0.033 | -4.1 to -4.7 | <= 17.6 | -0.15 to -0.18 / +0.02 |
| K(TC-F) + round trip <= 10% R | 114.4 | **+0.0003** | -0.0171 | -1.23 | 35.3 | -0.004 / +0.019 |

Full table: results.csv.

## What was learned
- Tape at entry is real but weak. A flip moves the loss off down sessions (-0.146 -> -0.02) but moves it onto up sessions,
  because the tape at the signal bar often reverses later in the day.
- Every flip still loses, because the signal has about zero gross edge in either direction. A long and a short on the same signal sum to -0.123R,
  which is the round-trip cost paid twice. A flip of a zero-edge signal is still zero edge minus costs.
- The re-break short (Sb) is worse than the immediate flip. By the time PDL breaks again, the move has already happened.
- The best curve is K(TC-F): breadth flip with a cost floor. It is flat on TRAIN (+0.0003), negative on VALID (-0.017), and 6 of 17 months are positive.
  It keeps 114 trades/session. Almost all of the lift comes from the cost floor (pdl1030/why angle 1), not from the tape.
- No variant passes, so I wrote no module.
