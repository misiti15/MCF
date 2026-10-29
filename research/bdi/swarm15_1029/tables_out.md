| # | setup | live n | live avg R | live w/o best day (share) | 2-yr avg R (TRAIN+VALID, n) | z live-bt | best variant | its TRAIN / VALID avg R | t (TRAIN+VALID) vs bar | d vs parent t (TRAIN / VALID) | HOLD (look) | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Failed Opening-Range-Low Break Long (0.05 ATR), `CWT14-failbrk-orl-p05-long` | 666 | -0.089 | -0.118 (total < 0) | -0.095 (84333) | +0.16 | S3 stop_x3.0 | -0.029 / -0.020 | -4.12 vs 4.84 | 8.1 / 6.8 | not looked | fail |
| 2 | Failed Prior-Day-Low Break Long (shallow), `CWT14-failbrk-pdl-p05-long` | 616 | -0.051 | -0.083 (total < 0) | -0.068 (53326) | +0.21 | S3 stop_x3.0 | -0.021 / -0.017 | -5.11 vs 4.84 | 8.2 / 7.3 | not looked | fail |
| 3 | Failed OR-Low Break Long (0.05 ATR, low volume), `CWT14-failbrk-orl-p05-lowvol-long` | 590 | -0.146 | -0.176 (total < 0) | -0.092 (59625) | -0.94 | S3 stop_x3.0 | -0.028 / -0.019 | -3.82 vs 4.84 | 7.3 / 6.4 | not looked | fail |
| 4 | Morning Bounce Fade (all day), `heat_fade_short-FD` | 479 | -0.126 | -0.182 (total < 0) | -0.030 (58329) | -0.80 | R3 first5_per_day | -0.003 / +0.021 | 0.17 vs 4.45 | 1.9 / 0.5 | not looked | fail |
| 5 | Coil Under the High (4 bars), `CWT12-coil-k4-long` | 421 | -0.070 | -0.094 (total < 0) | -0.073 (34840) | +0.05 | S3 stop_x3.0 | -0.017 / -0.024 | -3.13 vs 3.59 | 4.1 / 4.2 | not looked | fail |
| 6 | Failed PD-Low Break Long (0.05 ATR, low volume), `CWT14-failbrk-pdl-p05-lowvol-long` | 377 | -0.083 | -0.113 (total < 0) | -0.095 (35238) | +0.18 | S3 stop_x3.0 | -0.028 / -0.027 | -4.46 vs 4.84 | 7.6 / 6.6 | not looked | fail |
| 7 | Failed OR-Low Break Long (0.1 ATR), `CWT14-failbrk-orl-p10-long` | 361 | -0.062 | -0.083 (total < 0) | -0.090 (32195) | +0.65 | S3 stop_x3.0 | -0.032 / -0.015 | -3.20 vs 4.84 | 5.8 / 3.2 | not looked | fail |
| 8 | Failed Prior-Day-Low Break Long, `CWT14-failbrk-pdl-p10-long` | 349 | +0.001 | -0.048 (1 day) | -0.088 (29836) | +0.90 | S3 stop_x3.0 | -0.027 / -0.027 | -4.00 vs 4.84 | 6.5 / 6.2 | not looked | fail |
| 9 | Failed OR-Low Break Long (low volume), `CWT14-failbrk-orl-p10-lowvol-long` | 329 | -0.048 | -0.067 (total < 0) | -0.089 (25744) | +0.87 | S3 stop_x3.0 | -0.030 / -0.015 | -3.41 vs 4.84 | 5.9 / 4.5 | not looked | fail |
| 10 | Failed PD-High Break Short (0.05 ATR, low volume), `CWT14-failbrk-pdh-p05-lowvol-short` | 320 | -0.173 | -0.199 (total < 0) | -0.098 (35007) | -1.14 | S3 stop_x3.0 | -0.033 / -0.018 | -5.21 vs 4.84 | 10.9 / 7.0 | not looked | fail |
| 11 | Failed PD-High Break Short (0.1 ATR), `CWT14-failbrk-pdh-p10-short` | 317 | -0.217 | -0.281 (total < 0) | -0.091 (24154) | -1.26 | S3 stop_x3.0 | -0.029 / -0.012 | -3.66 vs 4.84 | 8.4 / 5.7 | not looked | fail |
| 12 | (no display name), `RW7-gapdn-bounce-early-short-FD` | 275 | -0.031 | -0.091 (total < 0) | -0.065 (20710) | +0.47 | S3 stop_x3.0 | -0.022 / -0.006 | -1.55 vs 4.76 | 3.9 / 1.3 | not looked | fail |
| 13 | (no display name), `RW2-exhaustion-noon-adv150-short-FD` | 260 | -0.311 | -0.372 (total < 0) | -0.066 (16976) | -2.52 | S3 stop_x3.0 | -0.020 / +0.007 | -0.91 vs 5.24 | 3.7 / 1.3 | not looked | fail |
| 14 | Opening-Range Low Sweep Reversal, `LIQ-orl-sweep-open15-s25-long` | 206 | -0.133 | -0.255 (total < 0) | -0.011 (10824) | -0.89 | C6 skip_prior_spy_abs_lt0.3 | -0.003 / +0.045 | 0.31 vs 4.23 | 0.9 / 2.0 | not looked | fail |
| 15 | Gap-Down Recovery Fade (all day), `L3-gap-slope-fromopen-FD` | 206 | +0.163 | -0.001 (1 day) | -0.017 (33873) | +1.36 | K2 cost_rt_le10pct | +0.097 / +0.019 | 1.13 vs 5.00 | 3.0 / 1.3 | +0.026 (n 5297, t 0.76) extra look | fail |

Family readout (rows that beat their parent on TRAIN and VALID / rows scored; median d vs parent per parent trade):

| family | rows | beat parent | exp > 0 TRAIN and VALID | median d (TRAIN) |
|---|---|---|---|---|
| context filter | 90 | 29 | 1 | +0.0338 |
| cost floor | 29 | 28 | 4 | +0.0547 |
| re-entry / caps | 45 | 5 | 0 | +0.0639 |
| stop x2/2.5/3 same $ | 39 | 36 | 3 | +0.0575 |
| target / scale-out | 25 | 2 | 0 | -0.0104 |
| entry window | 29 | 6 | 1 | +0.0128 |
| time stop 45/180 | 30 | 4 | 0 | +0.0005 |
