# arena-am-short (swarm 2026-10-17) - PLAN (written before any combination is scored)

*Educational only - not financial advice. History backtests only.*

Goal: SHORT entries, bar close 09:50-11:00 ET, built as AND-combinations (2-3 conditions) of arena indicators
(mcf/research/arena), starting from the single-indicator cells with the best TRAIN excess vs random
(research/swarm1017/arena/single_screen.parquet). Emit only passing combinations as lab modules.
Mirrors research/swarm1017/arena-am-long (same search design, short side) so the two can be compared.

## Prior evidence (read before scoring)
- In the arena screen, every short 09:50-11:00 cell with n >= 2000 has exp_r < 0 after costs (best atr_d_pct >= q95
  t1s1 -0.024R). The top "excess vs random" cells (atr_d_pct high, vwapDistPct high, ret1 high, dist_round_atr low)
  are mostly side-neutral composition (names where costs are small in R), not direction. Expectation: nothing passes.

## Data, split, costs (fixed)
- Rows: arena.data.build_month per open month (production R = gates.prod_r with tod entry costs, x3 on the extended
  tier; c_* = random same-minute control over the full adv20 >= $95M universe, computed before any subsetting),
  kept for bar close 09:50 <= tod < 11:00, live indicators only (context indicators are NaN in the live frame).
  Compact copy in scratch only (deleted at the end).
- TRAIN = 2024-10 + 2025-03..2025-12. VALID = 2026-01-01 onward. Locked block 2024-11..2025-02 never loaded.
- Trades: first qualifying bar per symbol-day in the window. Stats day-clustered. Regime = gates.session_regimes
  via history2y lib (up/flat/down).

## Search space (pre-declared; every scored configuration counts)
- Windows (3): (950,1100), (1000,1100), (950,1030).  Geometries (3): t05s1, t1s1, t1s05.
- Triggers T (30), mechanically from the screen, window 0950-1100, side SHORT, geom t1s1, live, n >= 2000:
  (a) best bin per indicator ranked by train excess vs random, top 20 indicators;
  (b) best bin per indicator ranked by dir_excess = (excess_short - excess_long)/2, top 10 indicators not in (a).
- Filters F (64): 16 slow/state indicators x 4 bins (<= q20, <= median, >= median, >= q80, train quantiles from
  the screen): gap_atr, atr_d_pct, prev_range_atr, day_vs_prev_range, rvol_day, from_pc_atr, dist_pdh_atr,
  dist_pdl_atr, rv12, day_range_atr, vwap_atr, fromOpen_atr, or_high_dist_atr, buyPressure, emaDiff, di_diff7.
  A filter on the trigger's own indicator is skipped (not counted).
- Stage 1 (pairs): every trigger x filter x window x geometry on TRAIN (~17,000).
- Stage 2 (triples): top 100 stage-1 pairs by train day-t (n_train >= 150) x each filter on a third indicator, TRAIN.
- Stage 3 (valid): only configurations passing the TRAIN screen gate are scored on VALID (same configuration on
  held-back data; not new configurations), then full combine.evaluate_combo on all open data.
- N_lineage = 20,282 (arena) + every configuration scored here. Bar = max(1.5, sqrt(2 ln N)).

## Gates
- TRAIN screen gate: n_train >= 150, exp_train > 0, excess_train > 0, train up AND down session exp > 0, both train
  halves (2024-10..2025-07 / 2025-08..2025-12) exp > 0.
- Candidate (combine.evaluate_combo quality_pass): n >= 200, exp > 0 train AND valid after costs, train t >= bar,
  regime gate, walk-forward share >= 0.6, beats random train AND valid, live-computable. Prefer >= 1 trade/day.
- Near-miss tier (reported, NOT candidates): passes everything except the t-bar.

## Outputs
results.csv, stage3.json, counts.json, NOTES.md, modules/ (only quality_pass). Scratch deleted at the end.

## Addendum (written after the main search, before the stability run)
Main search: 22,932 configurations, 0 quality_pass. Three near-misses (all gates except the t-bar) are checked for
parameter stability: N1 sma20_slope_pct/day_vs_prev_range/buyPressure t05s1, N2 vwapDistPct/day_vs_prev_range/di_diff7
t05s1, N3 rv12/day_vs_prev_range/from_pc_atr t05s1 (window 10:00-11:00). Each threshold is moved to its train
percentile -0.10 / 0 / +0.10 (27 threshold sets) x 3 geometries = 81 configurations per seed, 243 in total, all counted
in N. Stable = most neighbours positive on train AND valid. Diagnostic only: it cannot promote a near-miss to candidate.
