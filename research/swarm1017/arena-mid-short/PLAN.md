# arena-mid-short (swarm 2026-10-17) - PLAN (written before any combination is scored)

*Educational only - not financial advice. History backtests only.*

Goal: SHORT entries, bar close 11:00-14:00 ET, built as AND-combinations (2-3 conditions) of arena indicators
(mcf/research/arena), starting from the single-indicator cells with the best TRAIN excess vs random
(research/swarm1017/arena/single_screen.parquet, window 1100-1400, side short). Emit only passing combinations as lab
modules. Same design as research/swarm1017/arena-mid-long (code copied, side flipped) so the two are comparable;
includes the same separately-counted, research-only context branch (trigger + stock filter + market-state filter).

## Prior evidence (read before scoring)
- Screen, short 1100-1400 t1s1: the best cell is gap >= q95 (+2.15%) at +0.001R (t 0.02); its up-session exp is
  -0.285R and down +0.355R. Every short cell with n >= 2000 is negative in up sessions in the top list. The regime gate
  (up > 0) is the expected obstacle. Expectation: little or nothing passes.

## Data, split, costs (fixed)
- Rows: arena.data.build_month per open month (production R = gates.prod_r with tod entry costs, x3 on the extended
  tier; c_* = random same-minute control over the full adv20 >= $95M universe, computed before subsetting), kept for
  bar close 11:00 <= tod < 14:00, SHORT outcomes only, only the indicator columns the search uses. Scratch only
  (/tmp/.../scratchpad/swarm1017/arena-mid-short, deleted at the end).
- TRAIN = 2024-10 + 2025-03..2025-12. VALID = 2026-01-01 onward. Locked block 2024-11..2025-02 never loaded.
- Trades: first qualifying bar per symbol-day in the window. Stats day-clustered. Regime = history2y lib regimes()
  (gates.session_regimes, up/flat/down).

## Search space (pre-declared; every scored configuration counts)
- Windows (3): (1100,1400), (1100,1230), (1230,1400).  Geometries (3): t05s1, t1s1, t1s05.
- Triggers T (30), mechanically from the screen, window 1100-1400, SHORT, t1s1, live, n >= 2000 (common.py):
  (a) best bin per indicator by train excess vs random, top 20 indicators;
  (b) best bin per indicator by dir_excess = (excess_short - excess_long)/2, top 10 indicators not in (a).
- Live filters F (80): 20 slow/state indicators x 4 bins (<= q20, <= median, >= median, >= q80; train quantiles from
  the screen's 1100-1400 short bins): gap_atr, atr_d_pct, prev_range_atr, day_vs_prev_range, rvol_day, from_pc_atr,
  dist_pdh_atr, dist_pdl_atr, rv12, day_range_atr, vwap_atr, fromOpen_atr, or_high_dist_atr, buyPressure, emaDiff,
  di_diff7, sma50_dist_pct, adx7, day_pos, vwap_side_bars. Filter on the trigger's own indicator skipped (not counted).
- Stage 1 (pairs): every trigger x live filter x window x geometry on TRAIN.
- Stage 2 (triples): top 100 stage-1 pairs by train day-t with n_train >= 150 AND >= 60 train sessions x each live
  filter on a third indicator, TRAIN.
- Stage 2c (research-only context branch, counted): the same top 100 pairs x 5 context indicators (spy_fromOpen,
  qqq_fromOpen, breadth_vwap, spy_ret3, rs_spy) x 4 bins. live_supported = False; never a candidate here.
- Stage 3 (valid): configurations passing the TRAIN screen gate are scored on VALID (same configuration, held-back
  data), then the full combine.evaluate_combo on all open data for those positive on valid with excess > 0.
- Stage 4 (plateau, counted): for the best <= 3 near-misses, every threshold moved to the adjacent screen quantile
  (one at a time) and the other two geometries, to tell a plateau from a spike. VALID is then no longer clean for those.
- N_lineage = 20,282 (arena) + 23,032 (arena-am-long) + 30,773 (arena-mid-long) + arena-am-short (if its count is
  published before I finish) + every configuration scored here. Bar = max(1.5, sqrt(2 ln N)).

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
