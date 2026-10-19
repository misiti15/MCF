# tf1019/t2-cwt14 - results (Educational only - not financial advice)

99 configurations scored (11 setups x 5 timeframes as-is + 4 time-equivalent), core 80 symbols, min_adv 95M, t05s1,
production costs with time-of-day entry costs. Lineage N = 380,034 -> t bar 5.07 (family-only N=99 -> 3.03).
Parity: parameterised b3 (k=3) == cwt_live_lib.b3 == live module masks on 2026-09 1- and 5-min core frames.

**0 of 99 pass.** Highest overall exp_r of all 99 is -0.003R; every overall t is negative (best -0.13); 0 pass the regime
gate (longs lose in down sessions about -0.09..-0.23R, shorts lose in up sessions about -0.13..-0.23R); best WF share
0.59 (< 0.6). Only 2 of 99 have train exp > 0 and 5 of 99 have valid exp > 0; none has both.
No timeframe and no time-equivalent rescaling of the 3-bar reclaim window rescues any of the 11 setups. Live
Testing-2 data on these should be read with that in mind. No modules written.

Best timeframe per setup (highest t):

| setup | best tf (variant) | n | exp train | exp valid | t (need 5.07) | excess vs rnd | up / down | WF |
|---|---|---|---|---|---|---|---|---|
| orl-p05-long | 15m te | 10818 | -0.056 | -0.038 | -3.81 | -0.0001 | +0.081 / -0.166 | 0.18 |
| orl-p05-lowvol-long | 15m te | 5663 | -0.034 | -0.054 | -3.20 | -0.0016 | +0.107 / -0.155 | 0.12 |
| orl-p10-long | 10m te | 4745 | -0.068 | +0.009 | -1.81 | +0.0156 | +0.082 / -0.139 | 0.47 |
| orl-p10-lowvol-long | 10m te | 2790 | -0.053 | -0.051 | -2.56 | -0.0116 | +0.092 / -0.183 | 0.23 |
| pdh-p05-lowvol-short | 1m asis | 2097 | -0.069 | -0.047 | -3.11 | -0.0056 | -0.179 / +0.025 | 0.35 |
| pdh-p10-lowvol-short | 1m asis | 470 | +0.030 | -0.061 | -0.34 | +0.0390 | -0.173 / +0.138 | 0.59 |
| pdh-p10-short | 1m asis | 935 | +0.006 | -0.072 | -1.14 | -0.0011 | -0.132 / +0.077 | 0.53 |
| pdl-p05-long | 5m asis | 5849 | -0.029 | -0.040 | -2.57 | +0.0100 | +0.096 / -0.163 | 0.18 |
| pdl-p05-lowvol-long | 10m te | 2835 | -0.025 | -0.047 | -2.24 | +0.0076 | +0.079 / -0.160 | 0.23 |
| pdl-p10-long | 1m asis | 1141 | -0.062 | -0.018 | -1.67 | +0.0025 | -0.017 / -0.119 | 0.41 |
| pdl-p10-lowvol-long | 10m te | 1282 | -0.018 | +0.014 | -0.13 | +0.0365 | +0.080 / -0.091 | 0.35 |

Full grid: results.csv (all 99 rows: n, per_day, train/valid/forward exp, t, ctrl, excess, regimes, WF, fails).

Caveats: (1) the lowvol volumeRatio stays a 20-BAR mean in TE (20..300 min); frames start 09:50 so it cannot be
rebuilt like heat.py. (2) "OR" level = low/high of frame rows through the 10:00 bar; frames begin at the 09:50 bar
close, so research's "opening range" is ~09:45-10:00 on 5-min (09:49-10:00 on 1-min, 09:40-10:00 on 10-min), not
09:30-10:00 as the module docstrings say - true on the original history2y frames too; worth checking vs the live
implementation. (3) The live scale_out_r (pdl-p05-long 0.25, orl-p10-lowvol-long 0.35) is not modelled.
(4) Forward 10-08..10-16 is reported in results.csv only.
