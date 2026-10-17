# arena-pm-both (swarm 2026-10-17) - PLAN (written before any combination is scored)

*Educational only - not financial advice. History backtests only.*

Goal: LONG and SHORT entries, bar close 14:00-15:30 ET (the frames end at the 15:00 bar close, so in practice
14:00..15:00 inclusive, 13 decision bars), built as AND-combinations (2-3 conditions) of arena indicators
(mcf/research/arena), starting from the single-indicator cells with the best TRAIN excess vs random
(research/swarm1017/arena/single_screen.parquet, window 1400-1530). Emit only passing combinations as lab modules.
Same design as the sibling arena-am-*/arena-mid-* agents (comparable), run per side.

## Prior evidence (read before scoring)
- Screen, 1400-1530: best live cell gap_atr <= q05 short t1s1 (+0.087R, t 1.01) - regime-dependent and decays
  (valid -0.049R end to end). Best long cell macd_hist <= q05 t1s1 (+0.010R, t 0.34; down -0.095R).
  The random same-minute baseline here is about -0.06..-0.12R (costs + only ~1-2 h to the 15:55 time exit).
- Sibling AM/midday agents (am-long, am-short, mid-long; ~77k combos) found 0 quality passes. Expectation: little or
  nothing passes.

## Data, split, costs (fixed)
- Rows: arena.data.build_month per open month (production R = gates.prod_r with tod entry costs, x3 on the extended
  tier; c_* = random same-minute control over the full adv20 >= $95M universe, computed before subsetting), kept for
  bar close tod >= 1400 (<= 1500), both sides, only the indicator columns the search uses. Scratch only.
- TRAIN = 2024-10 + 2025-03..2025-12. VALID = 2026-01-01 onward. Locked block 2024-11..2025-02 never loaded.
- Trades: first qualifying bar per symbol-day in the window. Stats day-clustered. Regime = history2y lib regimes().

## Search space (pre-declared; every scored configuration counts), per side (long, short)
- Windows (3): (1400,1530) [= 14:00..15:00 incl], (1400,1430), (1430,1530).  Geometries (3): t05s1, t1s1, t1s05.
- Triggers T (30 per side), mechanically from the screen, window 1400-1530, that side, t1s1, live, n >= 2000:
  (a) best bin per indicator by train excess vs random, top 20 indicators;
  (b) best bin per indicator by dir_excess = (excess_side - excess_other)/2, top 10 indicators not in (a).
- Live filters F (80): 20 slow/state indicators x 4 bins (<= q20, <= median, >= median, >= q80; train quantiles from
  the screen's 1400-1530 bins): gap_atr, atr_d_pct, prev_range_atr, day_vs_prev_range, rvol_day, from_pc_atr,
  dist_pdh_atr, dist_pdl_atr, rv12, day_range_atr, vwap_atr, fromOpen_atr, or_high_dist_atr, buyPressure, emaDiff,
  di_diff7, sma50_dist_pct, adx7, day_pos, vwap_side_bars. Filter on the trigger's own indicator skipped (not counted).
- Stage 1 (pairs): trigger x live filter x window x geometry on TRAIN.
- Stage 2 (triples): top 100 stage-1 pairs per side by train day-t (n_train >= 150, >= 60 train sessions) x each
  live filter on a third indicator, TRAIN.
- Stage 2c (research-only context = market-regime filter branch, counted): same top 100 pairs x 5 context indicators
  (spy_fromOpen, qqq_fromOpen, breadth_vwap, spy_ret3, rs_spy) x 4 bins. live_supported = False; never a candidate.
- Stage 3 (valid): configurations passing the TRAIN screen gate are scored on VALID, then full
  combine.evaluate_combo on all open data for those positive on valid with excess > 0.
- Stage 4 (plateau, counted): for the best <= 3 near-misses, each threshold moved to adjacent screen quantiles and
  each geometry swapped, to tell a plateau from a spike (VALID no longer clean for those).
- N_lineage = 20,282 (arena) + 23,032 (am-long) + 22,932 (am-short) + 30,773 (mid-long) + every configuration here
  (+ arena-mid-short when its count is published). Bar = max(1.5, sqrt(2 ln N)).

## Gates
- TRAIN screen gate: n_train >= 150, train sessions >= 60, exp_train > 0, excess_train > 0, train up AND down
  session exp > 0, both train halves (2024-10..2025-07 / 2025-08..2025-12) exp > 0.
- Candidate (combine.evaluate_combo quality_pass): n >= 200, exp > 0 on train AND valid after costs, train t >= bar,
  regime gate (up AND down > 0), walk-forward share >= 0.6, beats random on train AND valid, live-computable.
  Preference >= 1 trade/day across the universe.
- Near-miss tier (reported, NOT candidates): everything except the t-bar.

## Outputs
results.csv, stage3.json, counts.json, NOTES.md, modules/ (quality_pass only), near_miss/ (labelled). Scratch deleted.
