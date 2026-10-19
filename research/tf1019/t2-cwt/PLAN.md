# tf1019/t2-cwt - Testing-2 CWT04/05/09/12/13 setups on 1/3/5/10/15-minute decision bars (pre-declared)

Declared 2026-10-19 (Sun 2026-10-18 night ET), before any scoring. Educational only - not financial advice.

## Setups (config/account_testing2.yaml; module, window, geometry, min_adv unchanged)
| setup | kernel (cwt_live_lib) | geom | window | min_adv |
|---|---|---|---|---|
| CWT04-backside-lh-a25-short / -a15-short | b1(a, trig=2) | t1s1 | [1030,1500] | 95M |
| CWT04-backside-vwaptest-a25-short | b1(2.5, trig=1) | t1s1 | [950,1500] | 95M |
| CWT04-backside-vwaptest-a15-short | b1(1.5, trig=1) | t1s05 | [950,1500] | 95M |
| CWT05-flush-m05/m075-v3/v5-long (4) | b5(m, v) | t05s1 | [950,1500] | 95M |
| CWT09-gapdn-vwaploss-g5-short | a7(5, trig=1) | t1s05 | [1030,1500] | 1M |
| CWT12-coil-k4-long / k6-long | b4a(nco) | t05s1 / t1s05 | [950,1130] | 95M |
| CWT12-flag-s1-long | b4b(1.0) | t05s1 | [950,1500] | 95M |
| CWT13-vwapstretch-z075-long | b2(0.75, long) | t1s1 | [950,1500] | 95M |
| CWT13-vwapstretch-z05-long | b2(0.5, long) | t05s1 | [1100,1500] | 95M |
| CWT13-vwapstretch-z075-short / z05-short | b2(z, short) | t1s1 | [1100,1500] | 95M |

NOT RUN (0 configurations): CWT09-gapdn-bounce-g5/g10-lowerhalf-short and CWT09-gapdn-vwaploss-g10-short - geometry "S" (structural stop, no target);
the timeframe frames carry only t1s1/t05s1/t1s05 outcomes and the rule is "keep the setup's geometry".
Live scale_out_r on CWT12-coil-k4-long (0.35) is not modelled (no scale-out outcome in the frames).

## Harness and universe
`mcf.research.timeframes.run_module_tf`, symbols="core" (80 symbols with all five timeframes), split "open"
(train 2024-10 + 2025-03..12; valid 2026-01..10-07; forward 10-08..10-16 reported only, never used to choose).
Locked block 2024-11..2025-02 never loaded or scored.
Known frame limit (all timeframes): frame rows start at the first bar closing >= 09:50 (15-min: 10:00), so session
state (HOD/LOD, runs, touches) starts there, not at 09:35 as live; the first bar covers 09:49/09:47/09:45/09:40/09:45-. Signals via numba ports (parity-checked vs cwt_live_lib at
the parent parameters on 2026-09 5-min core and a 1-min core subset before scoring).

## Variants
(a) AS-IS: module unchanged; bar-count parameters stay in BARS:
    - b5: 6-bar drop (6m minutes: 6/18/30/60/90), climax on one of the last 3 bars (3/9/15/30/45 min);
      vol_climax = volume / 20-BAR mean (20..300 min).
    - b4a: nco tight bars (k4: 4/12/20/40/60 min; k6: 6/18/30/60/90), mean range of up to 20 earlier bars
      (20..300 min), warm-up nco+6 bars.
    - b1, b2, b4b, a7: no bar-count lookbacks (state machines over session bars, prior-bar references, clock times).
(b) TIME-EQUIVALENT (TE), scaling to the 5-min clock time with round-half-up, min 1 bar:
    - b5: drop lookback round(30/m) bars, climax window round(15/m) bars -> m=1: 30/15, 3: 10/5, 10: 3/2, 15: 2/1.
      vol_climax stays a 20-BAR mean (frame feature; frames start at 09:50 so it cannot be rebuilt) - noted.
    - b4a: nco' = round(nco*5/m), mean-range window round(100/m), warm-up nco' + round(30/m)
      -> m=1/3/5/10/15: k4 nco 20, 7, 4, 2, 1; k6 nco 30, 10, 6, 3, 2; mean-range 100, 33, 20, 10, 7; warm-up +30, 10, 6, 3, 2.
    - b1, b2, b4b, a7: nothing to scale ("prior bar" / "next bar" structure is the pattern itself) -> no TE.
    m=5 TE == AS-IS (not counted twice).

## Configuration count (this task)
AS-IS 16 x 5 = 80; TE 6 (4 flush + 2 coil) x 4 = 24; total **104**. Nothing else is tuned.

## Bars (prior lineage from research/swarm1017/rework-cwt/counts.json: prior + that swarm), conservatively + all 104
- B1 (CWT04): 389,621 + 104 = 389,725 -> 5.07
- B2 (CWT13): 18,016 + 104 = 18,120 -> 4.43
- B4 (CWT12): 32,654 + 104 = 32,758 -> 4.56
- B5 (CWT05): 47,450 + 104 = 47,554 -> 4.64
- A7 (CWT09): 99,060 + 104 = 99,164 -> 4.80

## Gates (a candidate must pass ALL on its timeframe)
day-clustered t >= lineage bar and tf.summarize verdict gates (incl. regime up AND down > 0, n >= 30 each; walk-forward
share >= gates.WF_MIN_SHARE); exp_r > 0 on train AND on valid; excess vs the random same-minute baseline > 0.
Passing versions -> modules/ (parent copy + BAR_MINUTES = m).
