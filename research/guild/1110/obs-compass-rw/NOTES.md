Educational only — not financial advice.

# obs-compass-rw — is the compass's rest-of-day read more than arithmetic? (Observer, 2026-11-10 ~14:15 ET; owner COMPASS task, "try to break")

Inputs: the main-session study's `research/compass_5m/conditional_obs.csv.gz` (branch claude/charming-mccarthy-i3rhhr; 10-min marks
10:00-15:50, SPY fo, close side) + guild `research/compassbf/compass_2y.csv.gz` (W60 state at 15-min marks). No data GETs; market-only,
so no ledger rule change bears on it. **4 counted looks**: normal benchmark, empirical-distribution benchmark, compass-adds, prev-close.
`rw.py` -> `rw_out.txt`. Rows with >= 40 prior sessions of history: 13,663 (380 days, 2025-05..2026-11; locked block absent upstream).

**Benchmark (no same-day information):** P(SPY closes on the side of its open it is on now) = (1 + F(|fo|)) / 2, where F is the CDF of
|move from time T to the close| over the PRIOR 60 sessions at the same T. This is pure arithmetic: distance from the open against the
typical remaining move at that time of day.

## Findings (failures first)
1. **The rest-of-day read is arithmetic.** Empirical hold is 81.4% vs the benchmark's 81.0%; day-clustered difference **+0.4 pt, t 0.38**.
   Calibrated in every bin (0.555 -> 0.560, 0.654 -> 0.660, 0.755 -> 0.780, 0.857 -> 0.851, ... 0.997 -> 0.996). The famous climb
   "79% before 11:00 -> 92% after 13:00" is time decay of the remaining variance (normal-model prediction 66% -> 85% by block).
2. Against a NORMAL random walk, holds look +3.3 pt better (t 2.84). That gap is **fat tails** (many quiet afternoons), not trend
   persistence. It vanishes against the empirical distribution. Anyone quoting "beats a random walk" should use the empirical one.
3. **Compass state adds a little, unevenly.** At the same benchmark p, W60 confirmed-agree holds more in most bins (0.537 -> 0.626,
   0.636 -> 0.676, 0.711 -> 0.833, 0.836 -> 0.856), ~equal above 0.9. Overall confirmed +1.5 pt vs benchmark, leaning -1.9 pt.
   Day-level t's are inconsistent in sign with the row means (few rows per day), so: a hint, not a result.
4. **Previous close (owner's coupling):** on the same side of yesterday's close +1.0 pt vs benchmark (10,383 rows); opposite side
   -1.4 pt (3,280). A ~2.4-point effect, small.

## Suggested improvement for the owner's 'continuous conditional stats'
The cell table (time x fo bucket x prev-close side, n ~ 50 per cell) can be replaced by ONE continuous line with the same accuracy and
no sparse cells: "SPY is X% from its open at T; on the past 60 days the move from T to the close was smaller than that N% of the time
-> it finishes on this side about P%". Optionally add the +-1 pt prev-close nudge. It is honest by construction (calibrated, point-in-time)
and it makes plain that the compass's close-side number is mostly distance / time, not a direction forecast.
