# Timeframe swarm 2026-10-18/19: does the decision bar size matter?

*Educational only — not financial advice. Backtest results on the open history only; nothing here is paper or live.*

## Failures first

- **0 of 640 configurations pass.** No survivor, no module, no config change, no ledger entry.
- 82 setups were tested (84 setup rows across six families; MF3-FD, RW3-FD and RW5-FD were run by two families each and are counted twice, which is the conservative way round).
- Configurations: primary 108, t1-rw-st 95, t1-misc 126, t2-cwt 104, t2-cwt14 99, nearmiss 108 = **640** (420 as-is, 220 time-equivalent "TE").
- Bar per lineage: `max(1.5, sqrt(2 ln N_lineage))` with these 640 added: **4.43 to 5.25** (MF/NS 4.76, heat 4.78, CWT14 5.07, RW2/exhaustion 5.25). Even a swarm-only bar (N=640, which ignores the lineages' earlier searches) would be 3.59; one configuration with n >= 30 clears it (NM-HL-T75-pm-long 10m TE, t 3.66), and it is below its own lineage bar of 4.57.
- Regime gate (up AND down sessions both > 0, n >= 30 each): fails on almost every row; on the core-80 universe many rows fail because one regime has n < 30, which means "not shown", not "shown to fail".
- Random same-minute baseline: the baseline itself loses after costs on every timeframe (mean ctrl -0.04 to -0.07 R). Most setups beat it, but beating a losing baseline does not make a setup pay.
- Not tested: LIQ-orl/LIQ-pdl and CWT09 bounce g5/g10, vwaploss g10 (geometry S is not in the frames); orb20_a (not a lab class). Live refires/scale-outs (RW6G1, RWR3, coil-k4, pdl-p05, orl-p10-lowvol) are not modelled.
- Locked block 2024-11-01..2025-02-28 never loaded. Forward sessions 2026-10-08..10-16 were reported only and never used to choose.

## Setup and data

- Universe: the 80 "core" symbols that have all five timeframes (`research/history2y/data/frames_tf/symbols_core.txt`), each setup's own window, side, geometry (t1s1/t05s1/t1s05) and min_adv; production costs with time-of-day entry costs (`mcf/research/gates.py`); first qualifying bar per symbol-day.
- Splits: train 2024-10 + 2025-03..2025-12; valid 2026-01-01..2026-10-07; forward 2026-10-08..10-16 (7 sessions).
- **As-is:** the rule unchanged, lookbacks counted in bars (RSI14 = 14/42/70/140/210 minutes on 1/3/5/10/15-min bars; SMA50 = 50..750 minutes).
- **TE (time-equivalent):** lookbacks rescaled by 5/m to cover the same clock time as on 5-min bars, where the module exposes them (primary, t1-misc, t2-cwt CWT05/CWT12, t2-cwt14 reclaim window, nearmiss). t1-rw-st had no rescalable lookbacks.
- Parity checks: 5-min frames_tf reproduce history2y exactly (MF1-FD 46/46 trades); all TE builders reproduce frames at m=5; CWT kernels match cwt_live_lib 48/48.

## What the timeframe changes, in general (all families pooled, rows with n >= 30)

| bar | as-is rows | mean t | median t | share with exp > 0 | mean excess vs random R | mean random ctrl R |
|---|---|---|---|---|---|---|
| 1m | 81 | -1.59 | -1.42 | 12% | +0.012 | -0.062 |
| 3m | 82 | -0.92 | -0.74 | 27% | +0.028 | -0.044 |
| 5m (native) | 82 | -0.70 | -0.67 | 33% | +0.031 | -0.040 |
| 10m | 72 | -0.78 | -0.79 | 28% | +0.024 | -0.051 |
| 15m | 63 | -1.09 | -1.05 | 24% | +0.024 | -0.073 |

| bar | TE rows | mean t | share with exp > 0 |
|---|---|---|---|
| 1m | 33 | -0.98 | 30% |
| 3m | 52 | -0.93 | 31% |
| 10m | 55 | -1.28 | 20% |
| 15m | 51 | -1.30 | 25% |

Reading:
1. **1-minute bars hurt, clearly and consistently.** Every family is worst on 1m as-is: 3-8x more trades, worse expectancy, and the random baseline itself is most negative there. Faster decisions add noise trades, not edge.
2. **Longer bars (10/15m) do not help on average.** They neither rescue nor systematically hurt: the mean t is close to 5m, and trade counts fall below the point where the regime gate can be judged (median n 97 on 15m on core 80).
3. **5m is mildly best, but that is partly selection:** these setups were discovered on 5-min bars, so their thresholds are tuned to 5-min indicator scales. Even so, 5m was the best timeframe for only 16 of 82 setups; best-of-5 is spread evenly (1m 15, 3m 13, 5m 16, 10m 22, 15m 16), which is what noise looks like. Picking each setup's "best" timeframe is itself 5 tries.
4. **Time-equivalent lookbacks do not reproduce the 5-min signal.** On 1-3m bars rescaled RSI5/buyPressure become flatter (RSI5 spread 12 vs 26), so fixed thresholds rarely fire; on 10/15m they fire more often but at worse expectancy. A fair TE test needs percentile thresholds (backlog `tf1019-primary-te-thresholds`) — a new, separately counted family.
5. **Regime dependence is not a timeframe problem.** Shorts lose in up sessions and longs in down sessions on every bar size.

Closest to passing (all fail on t only, none is a candidate): NM-HL-T75-pm-long 10m TE (n 545, t 3.66 vs 4.57, up/down +0.13/+0.13, WF 0.69); NM-ETF-late-dip-di-long 5m as-is (n 194, t 3.12 vs 5.00). CWT04-lh-a25 5m reached t 5.32 on 19 trades, all in train: a small-sample artifact.

## Best timeframe per setup

Highest day-clustered t among configurations with n >= 30 (CWT04-lh-a25 and CWT04-vwaptest-a25 never reach n 30 and are omitted). Core 80 symbols, costs in, R after production costs. Fail codes: t = below lineage bar; train/valid = exp <= 0 in that split; regime = up/down gate; WF = walk-forward share < 0.6 or not computable; vs-random = excess <= 0. Every row fails.

| family | setup | best tf | lookbacks | n | exp train | exp valid | t (bar) | up / down R | vs random | WF | fails |
|---|---|---|---|---|---|---|---|---|---|---|---|
| primary | MF1 | 5m | asis | 90 | -0.132 | +0.032 | -0.66 (4.76) | -0.235 / -0.040 | -0.018 | 0.00 | t, train, regime, WF, vs-random |
| primary | MF2 | 3m | asis | 108 | -0.067 | +0.084 | 0.28 (4.76) | -0.195 / +0.132 | +0.052 | 1.00 | t, train, regime |
| primary | MF3 | 10m | asis | 35 | -0.214 | +0.077 | -0.51 (4.76) | -0.313 / +0.432 | -0.035 | - | t, train, regime, WF, vs-random |
| primary | MF3-FD | 10m | asis | 268 | -0.020 | -0.024 | -0.35 (4.76) | -0.040 / +0.202 | +0.002 | 0.61 | t, train, valid, regime |
| primary | MF4 | 1m | te | 318 | -0.018 | +0.033 | -0.03 (4.76) | -0.144 / +0.012 | +0.020 | 0.50 | t, train, regime, WF |
| primary | MF5 | 15m | asis | 97 | -0.053 | +0.224 | 0.34 (4.76) | -0.201 / +0.180 | +0.065 | 0.00 | t, train, regime, WF |
| primary | NS1 | 5m | asis | 45 | +0.099 | +0.180 | 1.61 (4.76) | +0.111 / +0.481 | +0.140 | - | t, regime, WF |
| primary | NS4 | 10m | asis | 42 | +0.062 | +0.014 | 0.15 (4.76) | +0.138 / -0.085 | +0.012 | - | t, regime, WF |
| primary | NS5 | 10m | te | 296 | -0.099 | +0.102 | -0.15 (4.76) | +0.282 / -0.187 | +0.087 | 0.60 | t, train, regime |
| primary | RW3-FD | 5m | asis | 338 | -0.025 | -0.016 | 0.06 (4.76) | -0.079 / +0.166 | +0.100 | 0.60 | t, train, valid, regime |
| primary | RW5-FD | 5m | asis | 326 | -0.047 | -0.076 | -0.93 (4.76) | -0.296 / +0.270 | -0.015 | 0.27 | t, train, valid, regime, WF, vs-random |
| primary | RW6G1 | 15m | te | 56 | +0.180 | +0.157 | 1.10 (4.76) | +0.036 / +0.421 | +0.075 | - | t, regime, WF |
| t1-misc | MF1-FD | 15m | asis | 190 | -0.051 | +0.064 | 0.01 (4.76) | -0.258 / +0.151 | +0.067 | 0.43 | t, train, regime, WF |
| t1-misc | MF2-FD | 15m | asis | 158 | -0.040 | +0.046 | -0.00 (4.76) | -0.189 / +0.115 | +0.102 | 0.60 | t, train, regime |
| t1-misc | MF3-FD | 10m | asis | 268 | -0.020 | -0.024 | -0.35 (4.76) | -0.040 / +0.202 | +0.002 | 0.61 | t, train, valid, regime |
| t1-misc | MF4-FD | 1m | te | 547 | -0.041 | +0.020 | -0.37 (4.76) | -0.159 / +0.034 | +0.016 | 0.50 | t, train, regime, WF |
| t1-misc | MF5-FD | 15m | asis | 97 | -0.053 | +0.224 | 0.34 (4.76) | -0.201 / +0.180 | +0.065 | 0.00 | t, train, regime, WF |
| t1-misc | NS1-FD | 3m | asis | 480 | +0.051 | +0.027 | 1.12 (4.76) | +0.098 / -0.051 | +0.056 | 0.56 | t, regime, WF |
| t1-misc | NS2-FD | 15m | te | 1152 | -0.024 | -0.044 | -0.86 (4.76) | -0.152 / +0.188 | +0.019 | 0.59 | t, train, valid, regime, WF |
| t1-misc | NS3-FD | 15m | asis | 339 | +0.083 | +0.016 | 0.73 (4.76) | -0.108 / +0.201 | +0.035 | 0.64 | t, regime |
| t1-misc | NS4-FD | 15m | asis | 40 | +0.181 | +0.199 | 1.02 (4.76) | +0.334 / +0.151 | +0.205 | - | t, regime, WF |
| t1-misc | NS5-FD | 3m | asis | 644 | -0.044 | +0.030 | -0.14 (4.76) | +0.172 / -0.096 | +0.011 | 0.65 | t, train, regime |
| t1-misc | heat_fade_long | 1m | te | 794 | -0.060 | +0.030 | -0.26 (4.78) | +0.057 / -0.041 | +0.075 | 0.56 | t, train, regime, WF |
| t1-misc | heat_fade_long-FD | 1m | asis | 4213 | -0.009 | -0.025 | -0.68 (4.78) | +0.115 / -0.121 | +0.032 | 0.47 | t, train, valid, regime, WF |
| t1-misc | heat_fade_short | 1m | te | 2617 | +0.043 | +0.017 | 0.82 (4.78) | -0.128 / +0.117 | +0.047 | 0.41 | t, regime, WF |
| t1-misc | heat_fade_short-FD | 10m | asis | 6971 | -0.013 | -0.021 | -0.90 (4.78) | -0.153 / +0.096 | +0.025 | 0.35 | t, train, valid, regime, WF |
| t1-rw-st | L3-gap-slope-fromopen | 15m | asis | 319 | +0.145 | +0.134 | 2.45 (5.03) | -0.005 / +0.607 | +0.125 | 0.88 | t, regime |
| t1-rw-st | L3-gap-slope-lowdist | 10m | asis | 303 | -0.054 | +0.067 | 0.16 (5.03) | -0.015 / +0.206 | +0.083 | 0.60 | t, train, regime |
| t1-rw-st | L3-gap-slope-rsi5hi | 10m | asis | 443 | -0.041 | +0.139 | 1.08 (5.03) | +0.066 / +0.025 | +0.065 | 0.83 | t, train |
| t1-rw-st | RW1-gapdn-bounce-flowsell-short | 10m | asis | 224 | +0.081 | +0.014 | 0.69 (4.95) | -0.108 / +0.223 | +0.043 | 0.44 | t, regime, WF |
| t1-rw-st | RW2-exhaustion-noon-adv150-short | 3m | asis | 3220 | -0.013 | +0.000 | -0.20 (5.25) | -0.175 / +0.232 | +0.044 | 0.41 | t, train, regime, WF |
| t1-rw-st | RW3-gapdn-rsi5pop-flowsell-short | 5m | asis | 322 | -0.025 | -0.016 | -0.38 (4.95) | -0.151 / +0.140 | +0.078 | 0.57 | t, train, valid, regime, WF |
| t1-rw-st | RW4-ns3-adv150-short | 15m | asis | 326 | +0.051 | +0.016 | 0.45 (4.83) | -0.107 / +0.171 | +0.016 | 0.60 | t, regime |
| t1-rw-st | RW5-heat30-flowsell-rsi5pop-gapdn-short | 5m | asis | 321 | -0.047 | -0.076 | -1.11 (4.95) | -0.337 / +0.264 | -0.023 | 0.27 | t, train, valid, regime, WF, vs-random |
| t1-rw-st | RW6-ns2-up3-short | 5m | asis | 421 | -0.002 | -0.052 | -0.51 (4.83) | -0.151 / +0.212 | -0.017 | 0.47 | t, train, valid, regime, WF, vs-random |
| t1-rw-st | RW7-gapdn-bounce-early-short | 10m | asis | 1106 | -0.042 | -0.034 | -0.93 (4.95) | -0.166 / +0.081 | -0.000 | 0.38 | t, train, valid, regime, WF, vs-random |
| t1-rw-st | ST1-ordn-long-pm-t05s1 | 10m | asis | 266 | +0.010 | +0.126 | 1.45 (4.97) | +0.167 / +0.156 | +0.106 | 0.73 | t |
| t1-rw-st | ST2-slope20up-long-am-t05s1 | 5m | asis | 1300 | -0.016 | +0.027 | 0.31 (4.97) | +0.039 / -0.064 | +0.031 | 0.53 | t, train, regime, WF |
| t1-rw-st | ST3-rsi5up-short-pm-t1s1 | 15m | asis | 41 | -0.225 | +0.389 | 1.14 (4.97) | -0.030 / +0.203 | +0.186 | - | t, train, regime, WF |
| t1-rw-st | ST4-emadn-long-am-t1s05 | 5m | asis | 165 | -0.047 | +0.119 | 0.55 (4.97) | +0.111 / -0.094 | +0.082 | 0.67 | t, train, regime |
| t1-rw-st | ST5-pdbrkup-short-mid-t05s1 | 1m | asis | 70 | -0.082 | +0.151 | 0.35 (4.97) | +0.063 / +0.057 | +0.163 | 1.00 | t, train, regime |
| t1-rw-st | ST6-volspikeup-short-mid-t1s1 | 5m | asis | 37 | -0.181 | +0.126 | 0.01 (4.97) | +0.319 / -0.038 | +0.127 | 1.00 | t, train, regime |
| t1-rw-st | ST7-rsi50dn-long-pm-t1s1 | 5m | asis | 78 | +0.199 | +0.047 | 1.06 (4.97) | +0.406 / +0.130 | +0.069 | - | t, regime, WF |
| t1-rw-st | ST8-volspikedn-long-pm-t1s1 | 5m | asis | 40 | +0.112 | +0.330 | 2.49 (4.97) | +0.259 / +0.154 | +0.219 | - | t, regime, WF |
| t1-rw-st | exhaustion_short | 3m | asis | 3270 | -0.019 | +0.000 | -0.31 (5.25) | -0.178 / +0.229 | +0.043 | 0.41 | t, train, regime, WF |
| t2-cwt | CWT04-backside-lh-a15-short | 10m | asis | 84 | +0.273 | -0.443 | 1.84 (5.07) | +0.153 / +0.490 | +0.141 | - | t, valid, regime, WF |
| t2-cwt | CWT04-backside-vwaptest-a15-short | 15m | asis | 122 | -0.231 | -0.416 | -2.62 (5.07) | -0.353 / -0.152 | -0.049 | - | t, train, valid, regime, WF, vs-random |
| t2-cwt | CWT05-flush-m05-v3-long | 15m | te | 172 | -0.039 | -0.076 | -0.45 (4.64) | +0.009 / -0.108 | +0.056 | 0.83 | t, train, valid, regime |
| t2-cwt | CWT05-flush-m05-v5-long | 3m | asis | 137 | +0.116 | +0.119 | 1.56 (4.64) | -0.002 / +0.200 | +0.135 | 1.00 | t, regime |
| t2-cwt | CWT05-flush-m075-v3-long | 15m | te | 76 | -0.002 | -0.019 | 0.33 (4.64) | +0.101 / -0.134 | +0.132 | - | t, train, valid, regime, WF |
| t2-cwt | CWT05-flush-m075-v5-long | 3m | te | 81 | +0.085 | +0.212 | 1.16 (4.64) | -0.006 / +0.229 | +0.178 | - | t, regime, WF |
| t2-cwt | CWT09-gapdn-vwaploss-g5-short | 5m | asis | 519 | +0.049 | -0.007 | 0.08 (4.80) | -0.180 / +0.159 | +0.019 | 0.33 | t, valid, regime, WF |
| t2-cwt | CWT12-coil-k4-long | 3m | te | 90 | +0.076 | +0.047 | 1.09 (4.56) | +0.259 / -0.071 | +0.065 | 0.67 | t, regime |
| t2-cwt | CWT12-coil-k6-long | 1m | asis | 175 | -0.030 | +0.029 | -0.18 (4.56) | +0.162 / -0.264 | +0.021 | 0.00 | t, train, regime, WF |
| t2-cwt | CWT12-flag-s1-long | 5m | asis | 158 | +0.042 | +0.005 | 0.43 (4.56) | +0.026 / +0.046 | +0.075 | 0.50 | t, WF |
| t2-cwt | CWT13-vwapstretch-z05-long | 1m | asis | 3073 | +0.042 | -0.002 | 0.54 (4.43) | +0.054 / +0.009 | +0.029 | 0.71 | t, valid |
| t2-cwt | CWT13-vwapstretch-z05-short | 3m | asis | 2013 | -0.028 | -0.005 | -0.69 (4.43) | -0.061 / +0.053 | +0.024 | 0.53 | t, train, valid, regime, WF |
| t2-cwt | CWT13-vwapstretch-z075-long | 10m | asis | 170 | +0.178 | +0.012 | 1.33 (4.43) | +0.096 / +0.078 | +0.081 | 1.00 | t, regime |
| t2-cwt | CWT13-vwapstretch-z075-short | 10m | asis | 114 | -0.034 | +0.060 | -0.20 (4.43) | -0.230 / +0.260 | +0.088 | 0.67 | t, train, regime |
| t2-cwt14 | CWT14-failbrk-orl-p05-long | 15m | te | 10818 | -0.056 | -0.038 | -3.81 (5.07) | +0.081 / -0.166 | -0.000 | 0.18 | t, train, valid, regime, WF, vs-random |
| t2-cwt14 | CWT14-failbrk-orl-p05-lowvol-long | 15m | te | 5663 | -0.034 | -0.054 | -3.20 (5.07) | +0.107 / -0.155 | -0.002 | 0.12 | t, train, valid, regime, WF, vs-random |
| t2-cwt14 | CWT14-failbrk-orl-p10-long | 10m | te | 4745 | -0.068 | +0.009 | -1.81 (5.07) | +0.082 / -0.139 | +0.016 | 0.47 | t, train, regime, WF |
| t2-cwt14 | CWT14-failbrk-orl-p10-lowvol-long | 10m | te | 2790 | -0.053 | -0.051 | -2.56 (5.07) | +0.092 / -0.183 | -0.012 | 0.23 | t, train, valid, regime, WF, vs-random |
| t2-cwt14 | CWT14-failbrk-pdh-p05-lowvol-short | 1m | asis | 2097 | -0.069 | -0.047 | -3.11 (5.07) | -0.179 / +0.025 | -0.006 | 0.35 | t, train, valid, regime, WF, vs-random |
| t2-cwt14 | CWT14-failbrk-pdh-p10-lowvol-short | 1m | asis | 470 | +0.030 | -0.061 | -0.34 (5.07) | -0.173 / +0.138 | +0.039 | 0.59 | t, valid, regime, WF |
| t2-cwt14 | CWT14-failbrk-pdh-p10-short | 1m | asis | 935 | +0.006 | -0.072 | -1.14 (5.07) | -0.132 / +0.077 | -0.001 | 0.53 | t, valid, regime, WF, vs-random |
| t2-cwt14 | CWT14-failbrk-pdl-p05-long | 5m | asis | 5849 | -0.029 | -0.040 | -2.57 (5.07) | +0.096 / -0.163 | +0.010 | 0.18 | t, train, valid, regime, WF |
| t2-cwt14 | CWT14-failbrk-pdl-p05-lowvol-long | 10m | te | 2835 | -0.025 | -0.047 | -2.24 (5.07) | +0.079 / -0.160 | +0.008 | 0.23 | t, train, valid, regime, WF |
| t2-cwt14 | CWT14-failbrk-pdl-p10-long | 1m | asis | 1141 | -0.062 | -0.018 | -1.67 (5.07) | -0.017 / -0.119 | +0.003 | 0.41 | t, train, valid, regime, WF |
| t2-cwt14 | CWT14-failbrk-pdl-p10-lowvol-long | 10m | te | 1282 | -0.018 | +0.014 | -0.13 (5.07) | +0.080 / -0.091 | +0.036 | 0.35 | t, train, regime, WF |
| nearmiss | NM-AMS-N1-quiet-morning-short | 3m | asis | 52 | +0.262 | +0.127 | 2.67 (4.62) | +0.382 / +0.207 | +0.194 | - | t, regime, WF |
| nearmiss | NM-AR-AM-gapdown-capitulation-long | 1m | te | 135 | +0.275 | +0.121 | 1.49 (4.62) | +0.322 / +0.334 | +0.149 | 0.40 | t, WF |
| nearmiss | NM-ETF-late-dip-di-long | 5m | asis | 194 | +0.229 | +0.035 | 3.12 (5.00) | +0.126 / +0.140 | +0.118 | 0.67 | t |
| nearmiss | NM-HL-T75-pm-long | 10m | te | 545 | +0.090 | +0.106 | 3.66 (4.57) | +0.128 / +0.126 | +0.106 | 0.69 | t |
| nearmiss | NM-PM-gapdn-above-pdh-rvol-short | 10m | te | 50 | +0.560 | +0.160 | 2.51 (4.89) | +0.469 / +0.247 | +0.246 | - | t, regime, WF |
| nearmiss | NM-RWN3-ns3-spyup-early-short | 3m | te | 51 | +0.067 | +0.164 | 0.77 (4.90) | -0.186 / +0.039 | +0.138 | - | t, regime, WF |
| nearmiss | NM-RWN4-ns2-spyup05-notfri-short | 1m | te | 42 | +0.238 | +0.236 | 2.91 (4.90) | +0.230 / +0.490 | +0.155 | - | t, regime, WF |
| nearmiss | NM-RWN5-ns3-mon-weakrs-short | 1m | te | 49 | +0.240 | +0.469 | 2.23 (4.90) | +0.365 / +0.735 | +0.396 | - | t, regime, WF |
| nearmiss | NM-RWR1-exh150-gapdn-spyup-pm-short | 3m | asis | 90 | +0.068 | +0.386 | 2.25 (5.25) | +0.168 / -1.016 | +0.068 | - | t, regime, WF |
| nearmiss | NM-RWR3-ns3-qqqup-early-short | 10m | asis | 36 | +0.258 | +0.212 | 1.30 (4.83) | +0.268 / -0.141 | +0.326 | - | t, regime, WF |
| nearmiss | NM-RWR4-ns2-up3-qqqup-slopedn-short | 10m | asis | 31 | +0.408 | +0.051 | 3.25 (4.83) | +0.289 / +0.487 | +0.126 | - | t, regime, WF |
| nearmiss | NM1-cwt09-g10-vwaploss-short | 3m | te | 41 | +0.226 | +0.199 | 1.54 (4.80) | +0.034 / +0.233 | +0.089 | - | t, regime, WF |

Source rows (all 640, every gate): `research/tf1019/{primary,t1-misc,t1-rw-st,t2-cwt,t2-cwt14,nearmiss}/results.csv`; per-family notes in each `NOTES.md`; full setup x timeframe grids in `primary/grid.md` and `nearmiss/grid.md`.

## Method caveats that apply to every row

- Core 80 symbols only: n is roughly 10% of full-universe counts for the near-miss setups, so power is low.
- frames_tf start at the first bar closing at or after 09:50 (10:00 on 15m), so session HOD/LOD/OR state misses 09:30-09:50 and differs by bar size (backlog `tf1019-t2cwt-pre0950-rows`, `tf1019-t2-cwt14-or-level-definition`).
- `mcf.research.arena.indicators.compute` assumes 5-min slots; nearmiss/run.py patched it per timeframe (backlog `tf1019-arena-grid-housekeeping`). Results from the other families do not use arena modules.
- context=True breadth is computed on the frame subset only (approximate).
- The 2026-10-07 session in the old history2y 5-min frames was built from a gappy download (SPY 357/390 bars); frames_tf use the complete re-fetch.

*Educational only — not financial advice.*
