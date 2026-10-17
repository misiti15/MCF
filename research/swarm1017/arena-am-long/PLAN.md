# arena-am-long (swarm 2026-10-17) - PLAN (written before any combination is scored)

*Educational only - not financial advice. History backtests only.*

Goal: LONG entries, bar close 09:50-11:00 ET, built as AND-combinations (2-3 conditions) of arena indicators
(mcf/research/arena), starting from the single-indicator cells with the best TRAIN excess vs random
(research/swarm1017/arena/single_screen.parquet). Emit passing combinations as lab modules.

## Data, split, costs (fixed)
- Rows: arena.data.build_month per open month (production R = gates.prod_r with tod entry costs, x3 on the extended
  tier; c_* = random same-minute control over the full adv20 >= $95M universe, computed before any subsetting),
  kept for bar close 09:50 <= tod < 11:00, live indicators only (context indicators are NaN in the live frame and are
  excluded from the search). Compact copy in scratch only.
- TRAIN = 2024-10 + 2025-03..2025-12. VALID = 2026-01-01 onward. Locked block 2024-11..2025-02 never loaded
  (data.months / lib.load_month refuse it).
- Trades: first qualifying bar per symbol-day in the window (gates.first_per_symbol_day). Stats day-clustered
  (gates.summary). Regime = gates.session_regimes via history2y lib (up/flat/down, open-history cut points).

## Search space (pre-declared; every scored configuration counts)
- Windows (3): (950,1100), (1000,1100), (950,1030).  Geometries (3): t05s1, t1s1, t1s05.
- Triggers T (<= 30), chosen mechanically from the screen, AM window 0950-1100, side long, geom t1s1, live, n >= 2000:
  (a) best bin per indicator ranked by train excess vs random, top 20 indicators;
  (b) best bin per indicator ranked by dir_excess (= (excess_long - excess_short)/2, the side-specific part), top 10
      indicators not already in (a). Each trigger keeps its screen bin (op, lo, hi).
- Filters F (64): 16 slow/context stock-state indicators x 4 bins (<= q20, <= median, >= median, >= q80; train
  quantiles from the screen's AM bins): gap_atr, atr_d_pct, prev_range_atr, day_vs_prev_range, rvol_day, from_pc_atr,
  dist_pdh_atr, dist_pdl_atr, rv12, day_range_atr, vwap_atr, fromOpen_atr, or_high_dist_atr, buyPressure, emaDiff,
  di_diff7. A filter on the same indicator as the trigger is skipped (not counted).
- Stage 1 (pairs): every trigger x filter x window x geometry, scored on TRAIN.
- Stage 2 (triples): the top 100 stage-1 pairs by train day-t (pre-declared, whatever their sign) x each filter on
  a third indicator (same window/geometry), scored on TRAIN.
- Stage 3 (valid): only configurations passing the TRAIN screen gate below are scored on VALID (those valid scores add
  no new configurations - same configuration, held-back data), then the full combine.evaluate_combo on all open data.
- N_lineage = 20,282 (arena) + every configuration scored here. Bar = max(1.5, sqrt(2 ln N)). Also reported with the
  related long lineages (bdi/longs1013 ~580, bdi/dips1013 ~80,187) added.

## Gates
- TRAIN screen gate (to reach VALID): n_train >= 150, exp_train > 0, excess_train > 0, train up-session exp > 0 and
  down-session exp > 0, both train halves (2024-10..2025-07 / 2025-08..2025-12) exp > 0.
- Candidate (quality_pass of combine.evaluate_combo): n >= 200, exp > 0 on train AND valid after costs, train t >= bar,
  regime gate (up AND down > 0, n >= 30 each, train+valid), walk-forward share >= 0.6, beats random on train AND valid,
  live-computable. Preference: >= 1 trade/day across the universe.
- Near-miss tier (reported, NOT candidates): everything except the t-bar.

## Outputs
results.csv (every scored configuration, train stats; valid stats where scored), finalists.json, NOTES.md,
modules/ (only quality_pass combinations). Scratch deleted at the end.
