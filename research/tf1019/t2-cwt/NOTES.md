# tf1019/t2-cwt - results (Educational only - not financial advice)

104 configurations scored (16 setups x 5 timeframes as-is = 80, + 24 time-equivalent for the 4 CWT05 flush and 2 CWT12
coil setups), core 80 symbols, each setup's own window / geometry / min_adv, production costs with time-of-day entry
costs, split "open" (train 2024-10 + 2025-03..12, valid 2026-01..10-07; forward 10-08..10-16 reported only).
Locked block 2024-11..2025-02 never loaded. Bars (lineage + all 104): B1/CWT04 5.07, B2/CWT13 4.43, B4/CWT12 4.56,
B5/CWT05 4.64, A7/CWT09 4.80. Parity: numba/param kernels == live module masks (cwt_live_lib) at parent parameters on
2026-09 core frames, 5-min (80 sym), 1-min (8 sym), 15-min (20 sym): 48/48 exact (parity.json; note CWT04 a2.5 had 0
live signals in that month, its kernel is shared with a1.5 which matched).
Not run (0 configs): CWT09-gapdn-bounce-g5/g10-lowerhalf-short and CWT09-gapdn-vwaploss-g10-short - geometry S
(structural stop), which the timeframe frames do not carry.

**0 of 104 pass.** Highest t on an honest sample is +1.84 (CWT04-lh-a15, 10m, n=84, valid -0.44R). The single row above
its bar (CWT04-lh-a25 5m, t 5.32) is 19 trades, all in train, none in valid: regime n<30, no WF folds -> fails.
8/104 have train AND valid > 0; 3/104 pass the regime gate; none of those clears even t 2. No timeframe and no
time-equivalent rescaling turns any of the 16 into a candidate. No modules written.

Best timeframe per setup (highest t; every row fails):

| setup | best tf | n | exp train | exp valid | t (bar) | excess vs rnd | up / down | main fail |
|---|---|---|---|---|---|---|---|---|
| CWT04-lh-a15-short | 10m | 84 | +0.273 | -0.443 | 1.84 (5.07) | +0.141 | +0.153 / +0.490 | t; valid<0 |
| CWT04-lh-a25-short | 5m | 19 | +0.612 | (0 trades) | 5.32 (5.07) | +0.205 | +0.571 / +0.963 | n=19, no valid, regime n |
| CWT04-vwaptest-a15-short | 15m | 122 | -0.231 | -0.416 | -2.62 | -0.049 | -0.353 / -0.152 | exp<0 |
| CWT04-vwaptest-a25-short | 5m | 23 | -0.154 | +0.276 | -0.60 | +0.184 | -0.232 / -0.413 | exp<0 |
| CWT05-flush-m05-v3-long | 15m TE | 172 | -0.039 | -0.076 | -0.45 | +0.056 | +0.009 / -0.108 | exp<0 |
| CWT05-flush-m05-v5-long | 3m | 137 | +0.116 | +0.119 | 1.56 (4.64) | +0.135 | -0.002 / +0.200 | t; regime |
| CWT05-flush-m075-v3-long | 15m TE | 76 | -0.002 | -0.019 | 0.33 | +0.132 | +0.101 / -0.134 | t; train<0 |
| CWT05-flush-m075-v5-long | 15m TE | 25 | +0.087 | +0.250 | 1.21 | +0.325 | +0.485 / -0.081 | t; n |
| CWT09-vwaploss-g5-short | 5m | 519 | +0.049 | -0.007 | 0.08 (4.80) | +0.019 | -0.180 / +0.159 | t; regime |
| CWT12-coil-k4-long | 3m TE | 90 | +0.076 | +0.047 | 1.09 (4.56) | +0.065 | +0.259 / -0.071 | t; regime |
| CWT12-coil-k6-long | 3m TE | 10 | -0.195 | +0.611 | 0.62 | +0.009 | +0.063 / -0.030 | n=10 |
| CWT12-flag-s1-long | 5m | 158 | +0.042 | +0.005 | 0.43 | +0.075 | +0.026 / +0.046 | t |
| CWT13-z05-long | 1m | 3073 | +0.042 | -0.002 | 0.54 (4.43) | +0.029 | +0.054 / +0.009 | t; valid<0 |
| CWT13-z05-short | 3m | 2013 | -0.028 | -0.005 | -0.69 | +0.024 | -0.061 / +0.053 | exp<0 |
| CWT13-z075-long | 10m | 170 | +0.178 | +0.012 | 1.33 (4.43) | +0.081 | +0.096 / +0.078 | t (regime n<30) |
| CWT13-z075-short | 10m | 114 | -0.034 | +0.060 | -0.20 | +0.088 | -0.230 / +0.260 | exp<0 |

Read-outs
- The 5-minute (current live) version is the best timeframe for only 4 of 16, and in each of those it is still ~0R.
- CWT12 coil as-is dies on long bars: 15m (k4, k6) and 10m (k6) give 0 trades (nco+6 bars do not fit before 11:30);
  TE on 1-min also gives 0 (20-30 consecutive tight 1-min bars never occur), TE 10/15m gives many trades at -0.05R.
- Bar-count lookbacks (as-is, reported): CWT05 6-bar drop = 6..90 min, 3-bar climax = 3..45 min, vol_climax 20-bar
  mean = 20..300 min (kept bar-based in TE; frame feature). CWT12 coil nco 4/6 bars = 4..90 min, 20-bar mean range.
  CWT04/09/12-flag/13 have no bar-count lookbacks (TE not applicable).
Caveats: (1) frame rows start at the first bar closing >= 09:50 (15-min 10:00), so session HOD/LOD/runs start there
on every timeframe, not 09:35 as live; the first bar spans 09:49/09:47/09:45/09:40/09:45 -> 09:50/10:00, so the
pre-09:50 coverage differs by timeframe (a confound for CWT04 run-from-open, CWT13 range, CWT12 touches).
(2) core 80 symbols only (highest dollar volume), so n is far below the live config comments (full universe).
(3) CWT12-coil-k4 live scale_out_r 0.35 not modelled. (4) Forward 10-08..10-16 in results.csv only.
Files: PLAN.md (pre-declared), run.py, parity.json, results.csv (all 104 rows incl. per-split, regime, WF, fails).
