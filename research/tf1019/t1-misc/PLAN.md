# tf1019/t1-misc - Testing-1 NS*-FD, MF*-FD, heat_fade_* on 1/3/5/10/15-minute decision bars (pre-declared)

Declared 2026-10-19 ~03:10 UTC (Sun 2026-10-18 ~23:10 ET), before any scoring. Educational only - not financial advice.

## Setups (config/account_testing.yaml / config/default.yaml; module, window, side, geometry unchanged)
| setup | module | window | side / geom | min_adv |
|---|---|---|---|---|
| NS1-FD | research/bdi/fullday/NS1-rsidip-rsi5pop-long-FD.py | 950-1500 | long t05s1 | 95M |
| NS2-FD | .../NS2-sma50break-overbought-short-FD.py | 950-1500 | short t1s1 | 95M |
| NS3-FD | .../NS3-failed-vwap-reclaim-short-FD.py | 950-1500 | short t1s1 | 95M |
| NS4-FD | .../NS4-pm-vwap-reclaim-oversold-short-FD.py | 950-1500 | short t1s05 | 95M |
| NS5-FD | .../NS5-sma50-flush-oversold-long-FD.py | 950-1500 | long t1s1 | 95M |
| MF1-FD..MF5-FD | research/bdi/fullday/MF{1..5}-*-FD.py | 950-1500 | short t1s05/t1s05/t1s1/t05s1/t1s1 | 95M |
| heat_fade_short | research/heat/candidates/regime_9.py (score <= SHORT_AT) | 950-1030 | short t1s1 | 125M |
| heat_fade_long | research/heat/candidates/regime_5.py (score >= LONG_AT) | 1105-1330 | long t1s1 | 125M |
| heat_fade_short-FD | research/bdi/fullday/heat_fade_short-FD.py | 950-1500 | short t1s1 | 125M |
| heat_fade_long-FD | research/bdi/fullday/heat_fade_long-FD.py | 950-1500 | long t1s1 | 125M |

heat_fade_* are `type: heat` (not lab). They are scored through a thin lab adapter (mask = formula score past its
threshold; HeatStrategy exit = stop 1R / target 1R, R = 0.25 x daily ATR = geometry t1s1), all inputs present in the
frames. Refire (NS1/NS3/MF2 live) is NOT modelled: first qualifying bar per symbol-day only.

SKIPPED (noted, not counted): LIQ-orl-sweep-open15-s25-long and LIQ-pdl-sweep-open15-vwap-long (GEOM "S" price-level
stop/target, plus BE/time-stop on LIQ-pdl; the harness carries t1s1/t05s1/t1s05 only, and the setups are defined on
15-minute sweep bars of a 09:30-10:00 range, so a "timeframe" change would be a different setup); orb20_a (class orb20,
not a lab module).

## Harness and universe
`mcf.research.timeframes.run_module_tf`, symbols="core" (80 symbols with all five timeframes), split "open"
(train 2024-10 + 2025-03..12; valid 2026-01..10-07; forward 10-08..10-16 reported, never used to pick). The locked
block 2024-11..2025-02 is never loaded or scored. Costs: production-cost R with time-of-day entry costs (gates).

## Variants
(a) AS-IS: module unchanged; lookbacks in BARS (RSI14 = 14 bars -> 14 min on 1-min, 210 min on 15-min; SMA50 = 50 bars
    -> 50 min .. 750 min; buyPressure 19 bars; heat inner lookbacks likewise).
(b) TIME-EQUIVALENT (TE): the modules expose no bar-count parameters (they read precomputed frame columns), so TE
    recomputes the columns the masks read - rsi, rsi5, buyPressure, sma50_dist_pct, heat and the heat components
    rsiHeat/momentumHeat/priceActionHeat/vwapHeat - with every lookback n -> max(2, round(n*5/m)) (same clock span as on
    5-minute bars), from the same 1-minute SIP cache (te_build.py, a copy of research/tf1019/primary/te_build.py plus the
    components). Parity at m=5: all 9 columns identical to the frames (max abs diff 0.0). Session features
    (vwapDistPct, fromOpen, gap, atr_d) and outcomes come from the frames. One-bar "cross" tests stay one decision bar.
    m=5 TE == AS-IS (not counted twice). rsi5 -> RSI(2) on 10- and 15-min bars (rounding floor of 2; noted).

## Configuration count (this task)
AS-IS 14 x 5 = 70; TE 14 x 4 = 56; total 126. Nothing else is tuned (no window, threshold or geometry changes).

## Bar t_required = max(1.5, sqrt(2 ln N_lineage)); N_lineage = prior + 126 (this task) + 108 (tf1019/primary, same lineages)
- MF lineage: 82,068 (research/bdi/rework1008/NOTES.md) + 234 = 82,302 -> 4.76
- NS lineage: 81,430 + 234 = 81,664 -> 4.76
- heat lineage: 19,200 (research/heat/HEAT_STUDY.md) + 74,056 (rework1008 swarm, conservatively counted) + 126 = 93,382 -> 4.79
- Informational: this task's family alone N=126 -> 3.11.

## Gates (a candidate must pass ALL on its timeframe)
day-clustered t >= t_req(N_lineage); exp_r > 0 overall, on train AND on valid; regime gate up AND down > 0 (n >= 30
each, tf.summarize); walk-forward share >= gates.WF_MIN_SHARE; excess vs the random same-minute baseline > 0
(tf.summarize verdict must be the passing verdict). Passing versions -> modules/ (parent copy + BAR_MINUTES = m).
