# arena-am-short (swarm 2026-10-17) - NOTES

*Educational only - not financial advice. These are history backtests only; nothing here is paper or live.*

## Failures first
- **Candidates: none.** 22,932 configurations were scored in the main search, plus 243 in the stability check, for
  23,175 here. **0 pass** combine.evaluate_combo quality_pass. `modules/` is empty.
- Lineage N = 20,282 (arena) + 23,175 = **43,457**. Bar = max(1.5, sqrt(2 ln N)) = **4.62**. No configuration that
  also held on VALID reached it. The one train t above 4.62 (6.65) collapsed on VALID.
- Funnel:
  - 412 pass the TRAIN screen gate (n >= 150, exp > 0, beats random, up > 0, down > 0, both train halves > 0).
  - 60 of those are positive on VALID with positive excess. They were fully evaluated in stage3.json.
  - 0 pass every gate.
  - Under noise, about 412 x 5% = 21 would show valid t > 1.65, so being positive on VALID is weak evidence by
    itself.
- **Overfit example.** sma20_slope_pct <= -0.74, dist_pdl_atr >= 0.96 and day_range_atr <= 0.52, short t1s1
  09:50-10:30:
  - TRAIN: +0.576R (n 253, t 6.65)
  - VALID: +0.025R (n 46)
  - Regime gate fails (up -0.117R). Walk-forward share is 0.
- **Single cells.** Every short 09:50-11:00 single cell in the arena screen with n >= 2000 was negative after costs.
  The best was atr_d_pct >= q95 at -0.024R. The triggers' "excess vs random" is mostly side-neutral composition.
- **Window redundancy.** Windows (950,1100) and (1000,1100) often give identical trades. Several indicators
  (di_diff7, rv12, day_vs_prev_range) evidently are not yet satisfiable at the 09:50 bar. These pairs were still
  counted as separate configurations, which is conservative.

## Near-misses (all gates except the t-bar). NOT candidates.
Window 10:00-11:00 for all three. Production costs, day-clustered statistics. The stability column is the share of
the 27 threshold sets at +/-10 train percentiles that are positive on both TRAIN and VALID, at the same geometry.

| id | conditions | geom | train exp / n / t | valid exp / n / t | up / down | WF | trades/day | stability |
|---|---|---|---|---|---|---|---|---|
| N1 | sma20_slope_pct <= -0.737, day_vs_prev_range <= 0.409, buyPressure >= 0.312 | t05s1 | +0.184 / 194 / 4.02 | +0.082 / 206 / 1.93 | +0.093 / +0.217 | 0.83 | 0.94 | 52% |
| N2 | vwapDistPct >= 0.918, day_vs_prev_range <= 0.409, di_diff7 <= 0 | t05s1 | +0.094 / 185 / 1.60 | +0.140 / 223 / 2.40 | +0.082 / +0.138 | 0.62 | 0.96 | 41% |
| N3 | rv12 >= 0.600, day_vs_prev_range <= 0.409, from_pc_atr <= -0.349 | t05s1 | +0.135 / 252 / 1.12 | +0.123 / 315 / 1.89 | +0.102 / +0.146 | 0.83 | 1.33 | 48% |

- **N1 is fragile.** Its neighbouring thresholds are positive on both splits only 52% of the time, and its t1s1 and
  t1s05 versions fail VALID.
- **N3's t1s05 neighbourhood is the most stable.** 85% of its 27 threshold sets are positive on both splits, with
  median +0.167R train and +0.065R valid. The seed itself at t1s05 fails the regime gate (up -0.027R). This is a
  rework lead, not an edge.
- **Common theme.** All three share **day_vs_prev_range <= 0.41**: a quiet morning, with today's range so far under
  41% of yesterday's range, shorted into strength or chop. This is a backlog hypothesis for a pre-registered test
  on forward data.
- Lab modules for N1, N2 and N3 are in `modules_nearmiss/`, clearly labelled NOT candidates. All their indicators
  are computable from the live LabStrategy frame. Parity holds: the module's mask on 2026-09 gives 20 symbol-days,
  the same as the arena's 20 trades. GEOM t05s1 is supported by LabStrategy. No exit features are needed beyond
  target/stop/15:55.

## Files
- PLAN.md (pre-declared search, plus an addendum written before the stability run)
- build.py, search.py, stability.py, nearmiss_eval.py
- results.csv: every main-search configuration, with valid stats for the train-gate survivors
- stage3.json, counts.json, stability.csv/json, nearmiss.json

## Data and split
- TRAIN = 2024-10 plus 2025-03..2025-12. VALID = 2026-01-01..2026-10.
- The locked block 2024-11..2025-02 was never loaded.
- Costs: gates.prod_r with time-of-day costs, x3 on the extended tier.
- The random baseline is the universe mean at the same minute.
- The scratch rows (1.5 GB) were deleted.
