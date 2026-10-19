# tf1019/t2-cwt14 - the 11 Testing-2 CWT14-failbrk setups on 1/3/5/10/15-minute decision bars (pre-declared)

Declared 2026-10-19 ~03:10 UTC (Sun 2026-10-18 23:10 ET), before any scoring. Educational only - not financial advice.

## Setups (config/account_testing2.yaml; module, window, geometry t05s1, min_adv 95,000,000 unchanged)
orl-p05-long [950,1500] · orl-p05-lowvol-long [950,1500] · orl-p10-long [950,1200] · orl-p10-lowvol-long [950,1500] ·
pdl-p05-long [950,1500] · pdl-p05-lowvol-long [950,1500] · pdl-p10-long [950,1500] · pdl-p10-lowvol-long [950,1500] ·
pdh-p05-lowvol-short [950,1500] · pdh-p10-lowvol-short [950,1500] · pdh-p10-short [950,1200].
All are `cwt_live_lib.b3(level, p, lowvol, side)`. Exits as scored by the harness (t05s1, flat 15:55); the live
scale_out_r on three of them is NOT modelled (frames carry no scale-out outcome) - noted, not tuned.

## Harness and universe
`mcf.research.timeframes.run_module_tf`, symbols="core" (80 symbols with all five timeframes), split "open"
(train 2024-10 + 2025-03..12; valid 2026-01..10-07; forward 10-08..10-16 reported only, never used to choose).
Locked block 2024-11..2025-02 never loaded or scored.

## Variants
(a) AS-IS: module unchanged. Bar-count parameters: the reclaim must happen within 3 BARS of the poke bar
    (= 3, 9, 15, 30, 45 minutes on 1/3/5/10/15-min bars); the lowvol filter reads volumeRatio = volume / 20-BAR mean
    (= 20, 60, 100, 200, 300 minutes).
(b) TIME-EQUIVALENT (TE): reclaim window k = max(1, round(15/m)) bars -> 15, 5, 3, 2, 1 bars (15, 15, 15, 20, 15 min;
    m=10 rounds 1.5 up to 2). Implemented as a parameterised copy of b3 (parity: k=3 must equal L.b3 exactly).
    NOT scaled (not simple): the lowvol volumeRatio 20-bar lookback - the frames start at 09:50 and end at 15:00, so a
    100-minute volume mean cannot be rebuilt from frame rows the way heat.py builds it; it stays 20 bars (noted).
    Level definitions (prior-day H/L; "OR" = session low/high through the 10:00 bar of the frame rows) are clock-based
    and unchanged. m=5 TE == AS-IS (not counted twice).

## Configuration count (this task)
AS-IS 11 x 5 = 55; TE 11 x 4 = 44; total **99**. Nothing else is tuned.

## Bar
CWT14 (cwt-b-b3) lineage: 379,935 prior (research/swarm1017/rework-cwt14/NOTES.md) + 99 = 380,034
-> t_required = max(1.5, sqrt(2 ln N)) = 5.07. Informational: this family alone N=99 -> 3.03.

## Gates (a candidate must pass ALL on its timeframe)
day-clustered t >= 5.07 and tf.summarize verdict gates (incl. regime up AND down > 0, n >= 30 each; walk-forward
share >= gates.WF_MIN_SHARE); exp_r > 0 on train AND on valid; excess vs the random same-minute baseline > 0.
Passing versions -> modules/ (parent copy + BAR_MINUTES = m).
