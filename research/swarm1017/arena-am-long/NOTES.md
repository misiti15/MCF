# arena-am-long (swarm 2026-10-17) - NOTES

*Educational only - not financial advice. These are history backtests only. Nothing here is paper or live.*

## Failures first
- **No candidate passes. modules/ is empty.** I scored 23,058 configurations, all LONG with bar close 09:50-11:00:
  - 17,064 pairs (30 triggers x 64 filters x 3 windows x 3 geometries)
  - 5,968 triples (the top 100 pairs x a filter on a third indicator)
  - 26 threshold neighbours of the best near-miss
- The lineage is the arena's 20,282 plus these 23,058, so N = 43,340. The bar is max(1.5, sqrt(2 ln N)) = **4.62**. If the related long lineages are added (bdi/longs1013 and bdi/dips1013), the bar becomes 4.84.
- Most of the search is negative after costs. Only 17% of configurations with n_train >= 200 have exp > 0.
- The highest TRAIN t values are spurious. The top cells (t 8 to 15) sit on 7 to 12 sessions, from vwapDistPct-low triples. Among cells with at least 60 days, the best TRAIN t is 4.03 (macdPct high & dist_pdl_atr <= 0.44 & rvol_day <= 0.65). That cell turns **negative on VALID** (-0.04R), and so do its siblings. It is the classic overfit pattern.
- Funnel through the gates:
  - 185 configurations passed the pre-declared TRAIN screen gate.
  - 32 of those were positive on VALID with excess over random > 0.
  - 0 reach the t-bar. The best TRAIN t among the 32 is 3.14 (n 177).
- Every one of the 32 fails `t_train>=bar`. Many also fail walk-forward (< 0.6) or the regime gate.
- In the single screen, long entries in down sessions are about -0.3R for nearly every indicator bin. The regime gate (down > 0) is the main obstacle for AM longs.

## Near-miss (NOT a candidate, research-only): gap-down capitulation dip-buy
Search result: `ret12 <= -1.61% & gap_atr <= -0.22 & rvol_day <= 0.65`, long t1s1.
- train +0.19R (n 696, t 1.27)
- valid +0.14R (n 1,138, t 2.12)
- up +0.32R, down +0.09R
- walk-forward 0.59

**Neighbourhood (neighbors.json, 27 points: each threshold moved to the adjacent screen quantiles).**
- With n >= 200 and rvol_day <= 0.65 or 0.80: 14 of 14 points are positive on both train and valid, and the effect grows as the gap and the sell-off get deeper.
- With the tightest rvol cut (rvol_day <= 0.43): the points are thin (n 49 to 1,052; 7 of 9 are under 200) and train-negative in 4 of 9. Two of the n >= 200 points there lose money on train.
- Plateau point I chose (`near_miss/AR-AM-gapdown-capitulation.py`): ret12 <= -1.6145, gap_atr <= -0.4056, rvol_day <= 0.80, t1s1:

| Split | n | Expectancy | t | Excess over random (t) |
|---|---|---|---|---|
| Train | 741 | +0.33R | 1.71 | 2.88 |
| Valid | 847 | +0.20R | 2.51 | 3.22 |
| All | 1,588 | +0.26R | 2.48 | 4.30 |

  - Regime: up +0.36R (t 3.3), down +0.35R (t 2.2), flat -0.10R
  - Walk-forward 0.647 (17 folds); 3.7 trades/day; 692 symbols
  - It passes every gate except the t-bar (train t 1.71 vs 4.62)
- **Caveats:**
  - ret12 is NaN before the 10:50 bar, so every entry is at 10:50 or 10:55. In practice the window is 10:50-11:00.
  - TRAIN is concentrated: 367 of 741 trades are in April 2025 (the tariff sell-off and rebound). The losing months are 2025-07, 2025-11, 2025-12 and 2026-08.
  - VALID was looked at to choose the plateau point, so VALID is not clean for this family any more. Only the lead's locked-block score (2024-11..2025-02) can test it.
  - The live runner can compute every indicator in it (arena indicators.compute on the LabStrategy frame), and the exit is the standard lab t1s1.
- Status: backlog idea / locked-block test, not live.

## Split, costs, data
- TRAIN = 2024-10 and 2025-03..2025-12. VALID = 2026-01-01..2026-10. The locked block was never loaded.
- Costs: arena.data.outcomes, i.e. gates.prod_r with tod entry costs, plus x3 costs on the extended tier.
- Random baseline: the same-minute universe mean over all adv20 >= $95M rows.
- One trade per symbol-day (first bar). Statistics are day-clustered.

## Files
- PLAN.md (pre-declared search)
- build.py (scratch rows)
- search.py
- results.csv (every configuration: train stats, plus valid stats for gate survivors)
- stage3.json (combine.evaluate_combo for the 32 valid-positive configurations)
- counts.json, neighbors.py/.json, nearmiss_detail.py/.json
- near_miss/AR-AM-gapdown-capitulation.py (lab module; mask verified on a history frame)

Duplicate configurations (the same triple in a different order, or the 950-1100 and 1000-1100 windows that give the same first bar) are counted as scored. This keeps N slightly conservative.
