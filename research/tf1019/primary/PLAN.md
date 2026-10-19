# tf1019/primary - the 12 Primary setups on 1/3/5/10/15-minute decision bars (pre-declared, written before any scoring)

Declared 2026-10-19 ~03:00 UTC (Sun 2026-10-18 22:55 ET), before any run. Educational only - not financial advice.

## Setups (config/default.yaml, enabled, Primary; module, window, geometry unchanged)
MF1 [950,1030] t1s05 · MF2 [950,1100] t1s05 · MF3 [950,1100] t1s1 · MF4 [950,1100] t05s1 · MF5 [950,1500] t1s1 ·
MF3-FD / RW3-FD / RW5-FD [950,1500] t1s1 · NS1 [950,1130] t05s1 · NS4 [1130,1500] t1s05 · NS5 [950,1130] t1s1 ·
RW6G1 [950,1130] t1s1 (live refire is NOT modelled: first qualifying bar per symbol-day only).

## Harness and universe
`mcf.research.timeframes.run_module_tf` (gates.lab_trades: first qualifying bar per symbol-day, production-cost R,
time-of-day entry costs), symbols="core" (80 symbols with all five timeframes; like-for-like), min_adv 95,000,000 (as
in config), split "open" (train 2024-10 + 2025-03..12; valid 2026-01..10-07; forward 10-08..10-16, never used to pick).
The locked block 2024-11..2025-02 is never loaded or scored.

## Variants
(a) AS-IS: module unchanged; lookbacks in BARS (RSI14 = 14 bars; on 15-min bars = 210 min, on 1-min = 14 min).
(b) TIME-EQUIVALENT (TE): the modules expose no bar-count parameters (they read precomputed frame columns), so TE
    recomputes the bar-count columns the 12 masks read - rsi, rsi5, buyPressure, sma50_dist_pct and heat (with ALL its
    inner lookbacks: RSI14, momentum shifts 4/9, EMA 9/21/12/26, volume 20, volumeSurge 5/15, pricePosition 20) - with
    every lookback n scaled to max(2, round(n * 5 / m)) so it spans the same clock time as on 5-minute bars, from the
    same 1-minute SIP cache (locked dates dropped at load). Session features (vwapDistPct, fromOpen, gap, atr_d) and
    outcomes are unchanged (taken from the frames). The one-bar "cross on this bar" tests (NS1/NS4/NS5/RW6G1) stay one
    decision bar. Parity check: the TE builder at m=5 must reproduce the frame columns. For m=5 TE == AS-IS (not
    counted twice). For m=15, rsi5 -> RSI(2) (rounding; noted).

## Configuration count (this task)
AS-IS 12 x 5 = 60; TE 12 x 4 = 48; total 108. Nothing else is tuned (no window, threshold or geometry changes).

## Bar (N_lineage = prior lineage count + 108, conservatively all 108 added to each lineage)
- MF lineage (MF1-5, MF3-FD, RW3-FD, RW5-FD): 82,068 (research/bdi/rework1008/NOTES.md) + 108 -> t_req 4.76
- NS lineage (NS1, NS4, NS5): 81,430 (same source) + 108 -> t_req 4.76
- RW6G1: ~81,950 (implied by its ledger t_required 4.757) + 108 -> t_req 4.76
- Informational only: this task's family alone N=108 -> 3.06. Other tf1019 swarm tasks add to N (not counted here).

## Gates (a candidate must pass ALL on its timeframe)
day-clustered t >= t_req(N_lineage); exp_r > 0 overall, on train AND on valid; regime gate up AND down > 0 (n >= 30
each, tf.summarize); walk-forward share >= gates.WF_MIN_SHARE; excess vs the random same-minute baseline > 0.
Forward (10-08..10-16) is reported, never used to choose. Passing versions -> modules/ (parent copy + BAR_MINUTES = m).
