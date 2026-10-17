# arena-mid-long (swarm 2026-10-17) - NOTES

*Educational only - not financial advice. History backtests only; nothing here is paper or live.*

## Failures first
- **No candidate passes. modules/ is empty.** I scored 30,773 configurations, all LONG with bar close 11:00-14:00:
  - 21,276 pairs (30 triggers x 80 live filters x 3 windows x 3 geometries, minus same-indicator pairs)
  - 7,476 live triples and 2,000 research-only context triples (the top 100 pairs x a third condition)
  - 21 plateau points around 3 near-misses
- N_lineage = 20,282 (arena) + 23,032 (arena-am-long) + 30,773 = **74,087**, so the bar is max(1.5, sqrt(2 ln N)) =
  **4.74** (4.92 with the old bdi/longs1013 + dips1013 lineages). arena-am-short ran at the same time and is NOT in this N.
- Funnel: 937 passed the TRAIN screen gate (646 live), 156 were positive on VALID with excess > 0 (75 live), and
  **0 pass quality_pass**. 14 fail only the t-bar (9 live); their best TRAIN t is 2.04.
- **Overfit is visible.** Configurations that clear the bar on TRAIN all turn negative on VALID, for example:

| Configuration (live) | Window, geometry | Train | Valid |
|---|---|---|---|
| gap <= -1.25% & day_range_atr >= 0.98 & day_vs_prev_range <= 0.54 | 11:00-14:00 t1s1 | +0.294R, n 576, t 6.17, up and down > 0 | **-0.154R**, n 273 |
| from_pc <= -3.4% & dist_pdl_atr >= 1.02 & rv12 >= 0.22 | 12:30-14:00 t1s1 | +0.441R, t 4.91 | **-0.134R** |
| dist_hod_atr >= 1.04 & fromOpen_atr >= 0.37 & gap_atr <= -0.22 | 12:30-14:00 t05s1 | t 5.42 | **-0.119R** |

- Midday longs lose in down sessions. Among configurations with n_train >= 200, only 26.5% have exp > 0 after costs
  on TRAIN, and only 11.8% are positive in down sessions. The regime gate is the main obstacle, as it was for AM longs.
- The context branch is research-only. Adding SPY, QQQ or breadth state did not produce a pass either (0 of 81
  valid-positive configurations). Its best results fail walk-forward: they are TRAIN-heavy (April 2025) and weak on VALID.

## Near-misses (NOT candidates; near_miss/ modules are labelled; VALID was used for the plateau, so it is no longer clean)
1. **AR-MID-gapup-pullback-pdh**: macdPct <= -0.476 & dist_pdh_atr <= 0.381 & gap_atr >= 0.246, 12:30-14:00, t05s1.
   - Train +0.060R (n 636, t 0.95). Valid +0.054R (n 555, t 1.15).
   - Excess over random: +0.086R on train, +0.087R on valid.
   - Regime: up +0.11R, but down only **+0.001R**.
   - Walk-forward 0.765. 2.8 trades/day.
   - The best day (2025-04-14) carries 41% of P/L. Without it, exp is +0.036R.
   - Neighbours are fragile: 5 of 7 threshold or geometry moves fail the regime gate, and macdPct -0.30 is valid-negative.
   - Verdict: a spike, not a plateau.
2. **AR-MID-momo-di-turn**: momentum <= -0.647 & di_diff7 >= 22.9 & rv12 >= 0.224, 11:00-14:00, t1s1.
   - Train +0.137R (n 161 < 200, t 1.70). Valid +0.130R (n 226).
   - Regime: up +0.24R, down +0.03R. Walk-forward 0.75. 0.9 trades/day.
   - The rv12 neighbours hold. The momentum neighbour (-0.42) is train-negative, and the di_diff7 neighbours fail the regime gate.
   - It is thin and concentrated in April 2025.
3. A sibling of family 1, with fromOpen_atr <= 0.012 instead of the gap filter: 4.3 trades/day, train +0.065R, valid +0.034R, down +0.001R. It has the same fragility.
- Both modules were checked on a raw history frame (2026-03): mask + gates.lab_trades reproduces the arena trades
  exactly (76 trades, +0.114R; 36 trades, +0.001R). Every indicator they use can be computed by the live LabStrategy frame,
  and the exits are the standard lab exits. **No exit feature is missing.**

## Split, costs, data
- TRAIN = 2024-10 + 2025-03..2025-12 (234 sessions). VALID = 2026-01-01..2026-10 (192 sessions). The locked block
  2024-11..2025-02 was never loaded.
- Costs: arena.data.outcomes, i.e. gates.prod_r with tod entry costs, plus x3 on the extended tier. The random baseline is
  the same-minute universe mean over the full adv20 >= $95M universe. Trades are the first bar per symbol-day. Statistics are day-clustered.
- Duplicates are counted as scored. Examples: z12 and bb_pctb12 low tails are the same rows, and the 11:00-14:00 window
  shares its first bars with 11:00-12:30. This keeps N conservative.
- Resources: the peak RSS of search.py was about 6.5 GB, a little over the 6 GB guideline, for about 5 minutes. Scratch (2.2 GB) was deleted.

## Files
- PLAN.md, common.py (pre-declared space), build.py, search.py, plateau.py
- results.csv (every configuration: train stats, plus valid stats for gate survivors), stage3.json (evaluate_combo of the 156)
- plateau.json, counts.json, near_miss/*.py
