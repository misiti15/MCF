# Replay calibration scorecard — HELD-OUT 2026-11-02..2026-11-16 (scored once)

*Educational only — not financial advice. Calibrated session replay (mcf/replay/livecal.py, params_v2) vs the live paper journals; targets pre-registered in TARGETS.md; R after LR8 costs on each side's own fills.*

| account | sessions | live trades | replay trades | match (exact bar) | match ±1 min | extra | R bias (95% CI, session-clustered) | not optimistic | daily R corr | sign agree | skip-reason match | worst day | all targets |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| primary | 11 | 545 | 533 | 73.9% FAIL | 73.9% | 23.9% FAIL | -0.0155 [-0.0427, 0.0116] FAIL | PASS | 0.906 | 91% FAIL | 73.2% FAIL | FAIL | **FAIL** |
| testing | 11 | 799 | 934 | 91.0% FAIL | 91.0% | 25.9% FAIL | -0.0053 [-0.0258, 0.0153] PASS | PASS | 0.993 | 91% PASS | 85.9% FAIL | FAIL | **FAIL** |
| testing2 | 11 | 1545 | 1805 | 89.7% FAIL | 89.7% | 27.1% FAIL | 0.0165 [0.0001, 0.0329] FAIL | FAIL | 0.988 | 100% PASS | 77.2% FAIL | FAIL | **FAIL** |
| pooled | 11 | 2889 | 3272 | 87.1% FAIL | 87.1% | 26.2% FAIL | 0.0051 [-0.0075, 0.0177] PASS | PASS | 0.945 | 94% FAIL | 77.7% FAIL | FAIL | **FAIL** |

Live R vs replay R (sum, after LR8 costs): primary -53.3 vs -69.0; testing -83.8 vs -55.3; testing2 -244.6 vs -236.6; pooled -381.7 vs -360.9

## Biggest status mismatches (matched signals, live -> replay)

- **primary**: skipped:max positions for this setup -> skipped:setup daily loss limit ×648; skipped:spread #bps > max -> submitted:ok ×87; submitted:ok -> skipped:setup daily loss limit ×79; skipped:spread #bps > max -> skipped:setup daily loss limit ×43; submitted:ok -> skipped:spread #bps > max ×19; submitted:ok -> skipped:spread is #% of stop distance ×19
- **testing**: skipped:spread #bps > max -> submitted:ok ×154; submitted:ok -> skipped:spread #bps > max ×32; skipped:spread is #% of stop distance -> submitted:ok ×26; submitted:ok -> skipped:spread is #% of stop distance ×25; skipped:cost filter -> skipped:spread is #% of stop distance ×14; skipped:split-tape short gate -> skipped:not shortable/ETB ×9
- **testing2**: skipped:spread #bps > max -> submitted:ok ×281; submitted:ok -> skipped:spread #bps > max ×69; skipped:spread is #% of stop distance -> submitted:ok ×66; submitted:ok -> skipped:spread is #% of stop distance ×41; skipped:spread #bps > max -> skipped:opposite side held ×26; skipped:spread #bps > max -> skipped:spread is #% of stop distance ×25

## Per setup (≥ 10 live trades: 42 setups, all listed)

| account | setup | live | replay | match | extra | live avg R | replay avg R | bias (matched) |
|---|---|---|---|---|---|---|---|---|
| primary | L3-gap-slope-fromopen-FD | 126 | 90 | 44% | 27% | 0.388 | 0.099 | -0.009 |
| primary | RW3-gapdn-rsi5pop-flowsell-short-FD | 92 | 98 | 83% | 24% | 0.050 | 0.134 | -0.064 |
| primary | RW5-heat30-flowsell-rsi5pop-gapdn-short-FD | 90 | 90 | 91% | 9% | -0.121 | -0.114 | -0.028 |
| primary | MF4-h40-open-flowsell-FD | 88 | 88 | 78% | 22% | -0.532 | -0.454 | -0.009 |
| primary | MF2-open-rsimidhi-flowsell-FD | 72 | 77 | 79% | 28% | -0.542 | -0.372 | 0.034 |
| primary | ST7-rsi50dn-long-pm-t1s1-FD | 23 | 26 | 78% | 35% | 0.202 | 0.219 | -0.037 |
| primary | L3-gap-slope-rsi5hi-FD | 21 | 32 | 86% | 67% | -0.507 | -0.402 | 0.011 |
| primary | NS5-sma50-flush-oversold-long | 17 | 14 | 76% | 6% | -0.252 | -0.325 | 0.043 |
| primary | NS1-rsidip-rsi5pop-long | 11 | 13 | 82% | 36% | -0.082 | -0.117 | 0.003 |
| testing | RW7-gapdn-bounce-early-short-FD | 238 | 282 | 91% | 28% | -0.066 | -0.081 | -0.030 |
| testing | GEN-261021-02-BarRngATRge0p14-PDLdistlem0p045-OPEN-SPYgt0p5-t1s1-long | 62 | 77 | 98% | 26% | -0.278 | -0.113 | 0.045 |
| testing | NS1-rsidip-rsi5pop-long-FD | 53 | 54 | 91% | 11% | -0.133 | -0.072 | -0.003 |
| testing | L3-gap-slope-rsi5hi-FD | 50 | 74 | 90% | 58% | 0.257 | 0.310 | 0.014 |
| testing | L3-gap-slope-lowdist-FD | 49 | 65 | 90% | 43% | 0.462 | 0.359 | 0.007 |
| testing | RW1-gapdn-bounce-flowsell-short-FD | 38 | 44 | 95% | 21% | 0.005 | 0.049 | -0.044 |
| testing | exhaustion_short | 36 | 36 | 94% | 6% | -0.218 | -0.172 | 0.047 |
| testing | CWT05-flush-m05-v3-long | 35 | 40 | 86% | 29% | -0.236 | -0.042 | -0.007 |
| testing | MF3-open-flowsell-rsi5hi | 31 | 32 | 90% | 13% | -0.226 | -0.061 | 0.017 |
| testing | intraday_momentum | 28 | 28 | 100% | 0% | -0.547 | -0.547 | 0.000 |
| testing | MF5-flowsell-vwapup-rsi5hi | 24 | 20 | 79% | 4% | -0.256 | -0.210 | 0.005 |
| testing | ST6-volspikeup-short-mid-t1s1-FD | 23 | 21 | 91% | 0% | -0.124 | -0.180 | -0.037 |
| testing | NS3-failed-vwap-reclaim-short | 20 | 29 | 85% | 60% | -0.405 | -0.330 | 0.045 |
| testing | MF4-h40-open-flowsell-FD | 19 | 31 | 89% | 74% | -0.342 | -0.525 | -0.021 |
| testing | MF2-open-rsimidhi-flowsell-FD | 14 | 15 | 86% | 21% | -0.412 | 0.006 | -0.029 |
| testing | exhaustion_short-FD | 12 | 14 | 100% | 17% | -0.221 | -0.175 | -0.046 |
| testing | orb20_a | 10 | 9 | 70% | 20% | 0.186 | 0.276 | 0.022 |
| testing2 | CWT14-failbrk-pdl-p10-long | 327 | 398 | 92% | 30% | -0.167 | -0.117 | 0.035 |
| testing2 | RW3S-gapdn-flowsell-short-FD | 220 | 273 | 81% | 43% | -0.341 | -0.236 | 0.000 |
| testing2 | CWT14-failbrk-pdl-p05-R2A-long | 202 | 233 | 91% | 25% | -0.107 | -0.099 | 0.015 |
| testing2 | CWT13-vwapstretch-z05-long | 160 | 170 | 91% | 15% | -0.254 | -0.235 | 0.020 |
| testing2 | CWT14-failbrk-pdl-p05-R2A-short | 138 | 163 | 89% | 29% | -0.060 | -0.031 | 0.019 |
| testing2 | CWT14-failbrk-pdl-p10-lowvol-long | 98 | 113 | 90% | 26% | -0.233 | -0.181 | 0.090 |
| testing2 | exhaustion_short-FD | 62 | 73 | 97% | 21% | -0.029 | -0.096 | -0.024 |
| testing2 | GEN-261026-07-Flow3ge0p56-BBpctge0p98-ADX7le34-PM-BRvwlt0p3-holdtr-short | 50 | 50 | 90% | 10% | 0.108 | 0.073 | -0.045 |
| testing2 | MF5-flowsell-vwapup-rsi5hi | 48 | 51 | 94% | 12% | 0.065 | 0.051 | 0.008 |
| testing2 | NS3V1-am-widestop-short | 41 | 53 | 95% | 34% | -0.007 | -0.004 | -0.006 |
| testing2 | RW1-gapdn-bounce-flowsell-short-FD | 39 | 48 | 90% | 33% | 0.064 | -0.018 | -0.053 |
| testing2 | NM-HL-T75-pm-long | 35 | 34 | 91% | 6% | -0.197 | -0.215 | 0.024 |
| testing2 | NM-AR-AM-gapdown-capitulation-long | 32 | 38 | 84% | 34% | -0.325 | -0.174 | 0.086 |
| testing2 | NM-MF3-qqqdn-gapdn-FD | 20 | 21 | 90% | 15% | -0.001 | -0.048 | -0.061 |
| testing2 | NS4-pm-vwap-reclaim-oversold-short | 11 | 12 | 100% | 9% | -0.179 | -0.276 | -0.004 |
| testing2 | CWT13-vwapstretch-z075-short | 10 | 10 | 90% | 10% | 0.216 | -0.019 | -0.029 |

## Daily R (account-session)

| account | day | live trades | replay trades | live R | replay R |
|---|---|---|---|---|---|
| primary | 2026-11-02 | 12 | 15 | -6.66 | -4.16 |
| primary | 2026-11-03 | 43 | 41 | +8.72 | +9.54 |
| primary | 2026-11-04 | 54 | 54 | -12.31 | -9.53 |
| primary | 2026-11-05 | 61 | 90 | +2.42 | -3.22 |
| primary | 2026-11-06 | 52 | 62 | -26.10 | -24.99 |
| primary | 2026-11-09 | 36 | 35 | -20.00 | -17.35 |
| primary | 2026-11-10 | 99 | 86 | -34.84 | -24.45 |
| primary | 2026-11-11 | 43 | 37 | -28.27 | -24.57 |
| primary | 2026-11-12 | 75 | 33 | +39.88 | +7.56 |
| primary | 2026-11-13 | 13 | 16 | -1.44 | -2.45 |
| primary | 2026-11-16 | 57 | 64 | +25.31 | +24.62 |
| testing | 2026-11-02 | 37 | 41 | -18.70 | -19.42 |
| testing | 2026-11-03 | 49 | 50 | +4.32 | +7.71 |
| testing | 2026-11-04 | 20 | 25 | -5.10 | -3.45 |
| testing | 2026-11-05 | 91 | 112 | +3.27 | +9.84 |
| testing | 2026-11-06 | 92 | 106 | +0.64 | +2.46 |
| testing | 2026-11-09 | 65 | 68 | -3.43 | +4.05 |
| testing | 2026-11-10 | 127 | 150 | -48.53 | -57.30 |
| testing | 2026-11-11 | 41 | 42 | -30.94 | -31.01 |
| testing | 2026-11-12 | 133 | 173 | +40.23 | +63.87 |
| testing | 2026-11-13 | 77 | 88 | -30.27 | -36.47 |
| testing | 2026-11-16 | 67 | 79 | +4.72 | +4.38 |
| testing2 | 2026-11-02 | 129 | 141 | -37.05 | -42.91 |
| testing2 | 2026-11-03 | 90 | 102 | +1.88 | +0.79 |
| testing2 | 2026-11-04 | 139 | 155 | -36.49 | -29.30 |
| testing2 | 2026-11-05 | 271 | 340 | -94.76 | -83.55 |
| testing2 | 2026-11-06 | 165 | 194 | -6.42 | -3.47 |
| testing2 | 2026-11-09 | 53 | 58 | -6.28 | -7.64 |
| testing2 | 2026-11-10 | 147 | 177 | -30.47 | -27.40 |
| testing2 | 2026-11-11 | 79 | 85 | -19.91 | -17.81 |
| testing2 | 2026-11-12 | 121 | 158 | +6.52 | +0.41 |
| testing2 | 2026-11-13 | 142 | 172 | -1.33 | -1.65 |
| testing2 | 2026-11-16 | 209 | 223 | -20.31 | -24.10 |

Educational only — not financial advice.
