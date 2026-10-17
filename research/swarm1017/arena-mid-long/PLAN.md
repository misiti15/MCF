# arena-mid-long (swarm 2026-10-17) - PLAN (written before any combination is scored)

*Educational only - not financial advice. History backtests only.*

Goal: LONG entries, bar close 11:00-14:00 ET, built as AND-combinations (2-3 conditions) of arena indicators
(mcf/research/arena), starting from the single-indicator cells with the best TRAIN excess vs random
(research/swarm1017/arena/single_screen.parquet, window 1100-1400). Emit only passing combinations as lab modules.
Same design as research/swarm1017/arena-am-long (comparable), moved to midday, with 4 more live filters and a
separately-counted, research-only context-filter branch (to measure what a market-state filter would be worth if the
live runner had SPY/breadth data).

## Prior evidence (read before scoring)
- Screen, long 1100-1400 t1s1: every live bin with n >= 2000 has exp_r between -0.21R and +0.03R after costs, and
  every one except gap_atr <= q05 (gap-down > 0.61 ATR) is negative in down sessions (-0.1..-0.4R). The regime gate
  (down > 0) is the main obstacle. Expectation: little or nothing passes.

## Data, split, costs (fixed)
- Rows: arena.data.build_month per open month (production R = gates.prod_r with tod entry costs, x3 on the extended
  tier; c_* = random same-minute control over the full adv20 >= $95M universe, computed before subsetting), kept for
  bar close 11:00 <= tod < 14:00, long outcomes only, only the indicator columns the search uses. Scratch only.
- TRAIN = 2024-10 + 2025-03..2025-12. VALID = 2026-01-01 onward. Locked block 2024-11..2025-02 never loaded.
- Trades: first qualifying bar per symbol-day in the window. Stats day-clustered. Regime = history2y lib regimes()
  (gates.session_regimes, up/flat/down).

## Search space (pre-declared; every scored configuration counts)
- Windows (3): (1100,1400), (1100,1230), (1230,1400).  Geometries (3): t05s1, t1s1, t1s05.
- Triggers T (30), mechanically from the screen, window 1100-1400, long, t1s1, live, n >= 2000:
  (a) best bin per indicator by train excess vs random, top 20 indicators;
  (b) best bin per indicator by dir_excess = (excess_long - excess_short)/2, top 10 indicators not in (a).
- Live filters F (80): 20 slow/state indicators x 4 bins (<= q20, <= median, >= median, >= q80; train quantiles from
  the screen's 1100-1400 bins): gap_atr, atr_d_pct, prev_range_atr, day_vs_prev_range, rvol_day, from_pc_atr,
  dist_pdh_atr, dist_pdl_atr, rv12, day_range_atr, vwap_atr, fromOpen_atr, or_high_dist_atr, buyPressure, emaDiff,
  di_diff7, sma50_dist_pct, adx7, day_pos, vwap_side_bars. Filter on the trigger's own indicator skipped (not counted).
- Stage 1 (pairs): every trigger x live filter x window x geometry on TRAIN.
- Stage 2 (triples): top 100 stage-1 pairs by train day-t with n_train >= 150 AND >= 60 train sessions (am-long's top
  t cells sat on 7-12 sessions) x each live filter on a third indicator, TRAIN.
- Stage 2c (research-only context branch, counted): the same top 100 pairs x 5 context indicators (spy_fromOpen,
  qqq_fromOpen, breadth_vwap, spy_ret3, rs_spy) x 4 bins. live_supported = False; never a candidate here.
- Stage 3 (valid): configurations passing the TRAIN screen gate are scored on VALID (same configuration, held-back
  data), then the full combine.evaluate_combo on all open data for those positive on valid with excess > 0.
- Stage 4 (plateau, counted): for the best <= 3 near-misses, every threshold moved to the adjacent screen quantile
  (one at a time), to tell a plateau from a spike. VALID is then no longer clean for those.
- N_lineage = 20,282 (arena) + 23,032 (arena-am-long, same family/design) + every configuration scored here.
  Bar = max(1.5, sqrt(2 ln N)). Also reported with the older long lineages (bdi/longs1013 + dips1013, ~102,021).

## Gates
- TRAIN screen gate: n_train >= 150, train sessions >= 60, exp_train > 0, excess_train > 0, train up AND down session
  exp > 0, both train halves (2024-10..2025-07 / 2025-08..2025-12) exp > 0.
- Candidate (combine.evaluate_combo quality_pass): n >= 200, exp > 0 on train AND valid after costs, train t >= bar,
  regime gate (up AND down > 0, n >= 30 each), walk-forward share >= 0.6, beats random on train AND valid, live.
  Preference >= 1 trade/day across the universe.
- Near-miss tier (reported, NOT candidates): everything except the t-bar.

## Outputs
results.csv (every configuration: train stats; valid where scored), stage3.json, counts.json, NOTES.md, modules/
(quality_pass only), near_miss/ (lab modules of near-misses, clearly labelled). Scratch deleted at the end.
