# Promotion / demotion review — 2026-10-19 (after the close)

Live paper results since each setup started, after costs. Testing 1 is missing 132 of today's 457 trades (state-save bug, fixed; they reload tomorrow).
Break-even = win rate needed at the setup's own avg win/loss size. t = confidence (about 2+ solid, under 1 could be luck).
Proposed rule (not yet approved): promote = avg R > 0 over ≥ 40 trades and ≥ 4 sessions and win rate above break-even; demote = avg R < 0 over ≥ 40 trades.

## Primary

| Setup | Live | Trades | Sessions | Win | Break-even | Avg R | t | Last 4 R | P/L |
|---|---|---|---|---|---|---|---|---|---|
| NS2-sma50break-overbought-short | off | 54 | 5 | 30% | 55% | -0.453 | -3.89 | -0.500 | $-792.48 |
| heat_fade_short | off | 48 | 3 | 35% | 52% | -0.305 | -2.27 | -0.305 | $-183.70 |
| heat_fade_long | off | 35 | 4 | 43% | 48% | -0.095 | -0.57 | -0.095 | $-68.11 |
| MF5-flowsell-vwapup-rsi5hi | on | 31 | 8 | 45% | 51% | -0.071 | -0.53 | -0.321 | $-8.77 |
| MF3-open-flowsell-rsi5hi | on | 29 | 8 | 52% | 56% | -0.069 | -0.39 | -0.426 | $-33.32 |
| MF3-open-flowsell-rsi5hi-FD | on | 25 | 2 | 52% | 60% | -0.137 | -0.78 | -0.137 | $19.25 |
| exhaustion_short | off | 23 | 4 | 35% | 55% | -0.256 | -1.68 | -0.256 | $-72.33 |
| MF4-h40-open-flowsell | on | 21 | 7 | 67% | 61% | +0.070 | 0.47 | +0.278 | $49.60 |
| MF1-945-flowsell-vwapup | on | 16 | 7 | 38% | 33% | +0.128 | 0.34 | -0.020 | $31.46 |
| NS5-sma50-flush-oversold-long | on | 10 | 5 | 50% | 35% | +0.262 | 0.75 | +0.208 | $25.22 |
| NS3-failed-vwap-reclaim-short | off | 9 | 2 | 33% | 62% | -0.326 | -1.44 | -0.326 | $-88.84 |
| orb20_a | off | 9 | 4 | 33% | 42% | -0.149 | -0.46 | -0.149 | $-247.64 |
| RW3-gapdn-rsi5pop-flowsell-short-FD | on | 8 | 2 | 62% | 54% | +0.120 | 0.41 | +0.120 | $19.55 |
| NS1-rsidip-rsi5pop-long | on | 6 | 4 | 67% | 73% | -0.088 | -0.28 | -0.088 | $-55.23 |
| NS4-pm-vwap-reclaim-oversold-short | on | 5 | 4 | 60% | 31% | +0.701 | 1.09 | +0.701 | $55.30 |
| MF2-open-rsimidhi-flowsell | on | 4 | 4 | 0% | – | -1.108 | -21.68 | -1.108 | $-48.63 |
| RW5-heat30-flowsell-rsi5pop-gapdn-short-FD | on | 4 | 2 | 75% | 30% | +0.588 | 1.71 | +0.588 | $23.88 |
| RW6G1-ns2-up3-vwap2sd-short | on | 3 | 1 | 0% | – | -1.033 | -179.98 | -1.033 | $-98.28 |

## Testing 1

| Setup | Live | Trades | Sessions | Win | Break-even | Avg R | t | Last 4 R | P/L |
|---|---|---|---|---|---|---|---|---|---|
| heat_fade_short-FD | on | 309 | 6 | 48% | 52% | -0.053 | -0.96 | -0.055 | $65.39 |
| RW7-gapdn-bounce-early-short-FD | on | 170 | 6 | 49% | 51% | -0.021 | -0.35 | +0.068 | $68.08 |
| RW2-exhaustion-noon-adv150-short-FD | on | 135 | 6 | 47% | 52% | -0.084 | -0.96 | -0.078 | $-115.26 |
| LIQ-orl-sweep-open15-s25-long | on | 126 | 5 | 44% | 48% | -0.082 | -0.93 | -0.296 | $-251.57 |
| heat_fade_long-FD | on | 111 | 6 | 24% | 56% | -0.537 | -6.85 | -0.564 | $-534.78 |
| heat_fade_long | on | 81 | 6 | 27% | 55% | -0.459 | -4.78 | -0.641 | $-394.44 |
| heat_fade_short | on | 77 | 6 | 46% | 57% | -0.222 | -1.77 | -0.206 | $23.35 |
| ST2-slope20up-long-am-t05s1-FD | on | 70 | 5 | 49% | 65% | -0.200 | -2.45 | -0.221 | $-239.47 |
| NS2-sma50break-overbought-short-FD | on | 66 | 5 | 30% | 56% | -0.436 | -4.28 | -0.496 | $-428.18 |
| L3-gap-slope-fromopen-FD | on | 47 | 5 | 43% | 50% | -0.138 | -0.93 | -0.188 | $-95.88 |
| NS3-failed-vwap-reclaim-short-FD | on | 41 | 5 | 51% | 43% | +0.141 | 0.9 | +0.126 | $109.85 |
| RW4-ns3-adv150-short-FD | on | 39 | 5 | 44% | 43% | +0.015 | 0.1 | +0.086 | $19.42 |
| RW6-ns2-up3-short-FD | on | 37 | 5 | 22% | 55% | -0.586 | -4.61 | -0.678 | $-325.89 |
| MF3-open-flowsell-rsi5hi-FD | on | 36 | 6 | 58% | 54% | +0.081 | 0.51 | +0.020 | $85.38 |
| RW1-gapdn-bounce-flowsell-short-FD | on | 33 | 6 | 36% | 47% | -0.174 | -1.14 | +0.008 | $-71.60 |
| MF1-945-flowsell-vwapup-FD | on | 32 | 6 | 38% | 42% | -0.106 | -0.45 | -0.365 | $5.43 |
| RW3-gapdn-rsi5pop-flowsell-short-FD | on | 31 | 6 | 71% | 47% | +0.354 | 2.57 | +0.325 | $135.72 |
| exhaustion_short-FD | on | 31 | 4 | 52% | 49% | +0.038 | 0.23 | +0.038 | $7.78 |
| RW5-heat30-flowsell-rsi5pop-gapdn-short-FD | on | 30 | 5 | 73% | 44% | +0.484 | 3.23 | +0.431 | $97.53 |
| MF5-flowsell-vwapup-rsi5hi-FD | on | 29 | 6 | 41% | 53% | -0.212 | -1.23 | -0.365 | $-14.73 |
| NS3-failed-vwap-reclaim-short | on | 25 | 3 | 52% | 48% | +0.083 | 0.39 | +0.083 | $20.14 |
| L3-gap-slope-rsi5hi-FD | on | 24 | 4 | 58% | 64% | -0.084 | -0.53 | -0.084 | $-71.33 |
| MF4-h40-open-flowsell-FD | on | 24 | 6 | 92% | 72% | +0.292 | 3.0 | +0.306 | $79.91 |
| ST1-ordn-long-pm-t05s1-FD | on | 23 | 4 | 30% | 70% | -0.582 | -4.01 | -0.582 | $-251.15 |
| MF2-open-rsimidhi-flowsell-FD | on | 21 | 5 | 57% | 43% | +0.325 | 1.04 | +0.520 | $65.14 |
| L3-gap-slope-lowdist-FD | on | 19 | 3 | 37% | 41% | -0.071 | -0.33 | -0.071 | $-37.14 |
| exhaustion_short | on | 16 | 4 | 38% | 33% | +0.105 | 0.23 | +0.105 | $-64.31 |
| NS5-sma50-flush-oversold-long-FD | on | 13 | 5 | 38% | 73% | -0.480 | -2.33 | -0.642 | $-158.29 |
| RW6G1-ns2-up3-vwap2sd-short-FD | on | 11 | 5 | 36% | 56% | -0.282 | -1.17 | -0.421 | $-65.01 |
| NS1-rsidip-rsi5pop-long-FD | on | 10 | 4 | 70% | 75% | -0.070 | -0.31 | -0.070 | $-18.61 |
| ST4-emadn-long-am-t1s05-FD | on | 9 | 3 | 11% | 30% | -0.662 | -1.75 | -0.662 | $-65.26 |
| RW2-exhaustion-noon-adv150-short | off | 8 | 1 | 62% | 58% | +0.075 | 0.23 | +0.075 | $24.24 |
| ST7-rsi50dn-long-pm-t1s1-FD | on | 7 | 4 | 71% | 53% | +0.194 | 0.85 | +0.194 | $12.10 |
| MF5-flowsell-vwapup-rsi5hi | off | 5 | 1 | 40% | 57% | -0.163 | -0.57 | -0.163 | $-3.80 |
| intraday_momentum | on | 5 | 3 | 80% | 23% | +0.153 | 2.19 | +0.153 | $1.94 |
| orb20_a | on | 5 | 4 | 60% | 12% | +0.435 | 1.31 | +0.435 | $3.01 |
| NS5-sma50-flush-oversold-long | off | 4 | 1 | 75% | 62% | +0.200 | 0.45 | +0.200 | $13.14 |
| ST8-volspikedn-long-pm-t1s1-FD | on | 4 | 2 | 50% | 63% | -0.165 | -0.42 | -0.165 | $-21.07 |
| MF3-open-flowsell-rsi5hi | off | 3 | 1 | 33% | 68% | -0.547 | -1.04 | -0.547 | $-22.23 |
| NS1-rsidip-rsi5pop-long | off | 3 | 1 | 100% | – | +0.526 | 16.49 | +0.526 | $13.59 |
| RW1-gapdn-bounce-flowsell-short | off | 3 | 1 | 33% | 54% | -0.383 | -0.62 | -0.383 | $-9.08 |
| ST2-slope20up-long-am-t05s1 | off | 3 | 1 | 33% | 62% | -0.267 | -0.67 | -0.267 | $-16.19 |
| L3-gap-slope-rsi5hi | off | 2 | 1 | 100% | – | +0.502 | 12.65 | +0.502 | $12.35 |
| NS4-pm-vwap-reclaim-oversold-short-FD | on | 2 | 2 | 100% | – | +1.803 | 5.2 | +1.803 | $24.38 |
| RW7-gapdn-bounce-early-short | off | 2 | 1 | 100% | – | +1.059 | 11.37 | +1.059 | $10.26 |
| ST6-volspikeup-short-mid-t1s1-FD | on | 2 | 1 | 100% | – | +0.510 | 1.04 | +0.510 | $10.13 |
| L3-gap-slope-fromopen | off | 1 | 1 | 0% | – | -1.080 | – | -1.080 | $-17.78 |
| LIQ-pdl-sweep-open15-vwap-long | on | 1 | 1 | 0% | – | -1.036 | – | -1.036 | $-2.71 |
| MF4-h40-open-flowsell | off | 1 | 1 | 0% | – | -0.167 | – | -0.167 | $-1.10 |
| RW3-gapdn-rsi5pop-flowsell-short | off | 1 | 1 | 0% | – | -1.128 | – | -1.128 | $-3.50 |
| RW5-heat30-flowsell-rsi5pop-gapdn-short | off | 1 | 1 | 100% | – | +1.271 | – | +1.271 | $8.80 |
| ST5-pdbrkup-short-mid-t05s1-FD | on | 1 | 1 | 100% | – | +3.362 | – | +3.362 | $9.44 |
| ST8-volspikedn-long-pm-t1s1 | off | 1 | 1 | 100% | – | +0.363 | – | +0.363 | $6.16 |

## Testing 2

| Setup | Live | Trades | Sessions | Win | Break-even | Avg R | t | Last 4 R | P/L |
|---|---|---|---|---|---|---|---|---|---|
| CWT14-failbrk-orl-p05-long | on | 352 | 6 | 60% | 69% | -0.117 | -3.08 | -0.141 | $-348.59 |
| CWT14-failbrk-orl-p05-lowvol-long | on | 341 | 6 | 55% | 71% | -0.216 | -5.51 | -0.239 | $-544.72 |
| CWT14-failbrk-pdl-p05-long | on | 229 | 6 | 58% | 66% | -0.111 | -2.15 | -0.224 | $-195.65 |
| CWT14-failbrk-orl-p10-long | on | 185 | 6 | 61% | 71% | -0.141 | -2.46 | -0.175 | $-221.97 |
| CWT14-failbrk-pdl-p10-long | on | 175 | 6 | 62% | 71% | -0.129 | -2.31 | -0.283 | $-155.38 |
| CWT14-failbrk-pdh-p05-lowvol-short | on | 174 | 6 | 62% | 67% | -0.074 | -1.27 | -0.103 | $-68.08 |
| CWT14-failbrk-orl-p10-lowvol-long | on | 172 | 6 | 63% | 70% | -0.112 | -2.0 | -0.242 | $-119.67 |
| CWT14-failbrk-pdl-p05-lowvol-long | on | 168 | 6 | 60% | 68% | -0.115 | -2.02 | -0.183 | $-265.35 |
| CWT12-coil-k4-long | on | 167 | 6 | 65% | 69% | -0.052 | -0.86 | -0.077 | $-157.99 |
| CWT14-failbrk-pdh-p10-short | on | 157 | 6 | 66% | 69% | -0.045 | -0.76 | -0.153 | $-11.30 |
| CWT14-failbrk-pdh-p10-lowvol-short | on | 87 | 5 | 57% | 68% | -0.154 | -1.85 | -0.172 | $-56.37 |
| CWT14-failbrk-pdl-p10-lowvol-long | on | 87 | 6 | 72% | 71% | +0.025 | 0.34 | -0.072 | $-15.15 |
| CWT13-vwapstretch-z05-short | on | 46 | 4 | 35% | 55% | -0.317 | -2.57 | -0.317 | $-132.65 |
| CWT09-gapdn-bounce-g5-lowerhalf-short | on | 42 | 4 | 14% | 38% | -0.584 | -3.68 | -0.584 | $-668.53 |
| CWT12-coil-k6-long | on | 42 | 5 | 33% | 35% | -0.053 | -0.23 | +0.168 | $-39.42 |
| CWT09-gapdn-vwaploss-g5-short | on | 29 | 3 | 10% | 33% | -0.702 | -3.85 | -0.702 | $-227.82 |
| CWT13-vwapstretch-z05-long | on | 25 | 4 | 48% | 70% | -0.286 | -2.07 | -0.286 | $-77.17 |
| CWT05-flush-m05-v3-long | on | 11 | 5 | 64% | 70% | -0.090 | -0.4 | +0.001 | $-30.87 |
| CWT13-vwapstretch-z075-long | on | 8 | 4 | 75% | 58% | +0.217 | 0.84 | +0.217 | $12.06 |
| CWT05-flush-m075-v3-long | on | 7 | 3 | 71% | 64% | +0.119 | 0.36 | +0.119 | $-3.17 |
| CWT12-flag-s1-long | on | 7 | 2 | 29% | 66% | -0.424 | -1.69 | -0.424 | $-16.39 |
| NM-HL-T75-pm-long | on | 6 | 1 | 50% | 57% | -0.075 | -0.3 | -0.075 | $-7.81 |
| NM-RWN5-ns3-mon-weakrs-short | on | 5 | 1 | 80% | 61% | +0.339 | 0.93 | +0.339 | $35.52 |
| CWT05-flush-m05-v5-long | on | 4 | 2 | 25% | 53% | -0.562 | -1.13 | -0.562 | $-25.80 |
| CWT09-gapdn-bounce-g10-lowerhalf-short | on | 4 | 3 | 25% | 72% | -0.472 | -1.47 | -0.472 | $-21.76 |
| CWT04-backside-vwaptest-a15-short | on | 3 | 2 | 0% | – | -1.046 | -4.12 | -1.046 | $-9.25 |
| CWT05-flush-m075-v5-long | on | 3 | 1 | 33% | 55% | -0.429 | -0.66 | -0.429 | $-13.03 |
| CWT09-gapdn-vwaploss-g10-short | on | 2 | 1 | 0% | – | -0.650 | -1.73 | -0.650 | $-54.93 |
| CWT13-vwapstretch-z075-short | on | 2 | 1 | 50% | 74% | -0.323 | -0.48 | -0.323 | $-10.39 |
| NM-RWN3-ns3-spyup-early-short | on | 2 | 1 | 50% | 59% | -0.164 | -0.17 | -0.164 | $-5.98 |
| NM-RWR3-ns3-qqqup-early-short | on | 2 | 1 | 50% | 59% | -0.164 | -0.17 | -0.164 | $-5.98 |
| CWT04-backside-lh-a15-short | on | 1 | 1 | 100% | – | +0.637 | – | +0.637 | $4.48 |
| NM-ETF-late-dip-di-long | on | 1 | 1 | 100% | – | +0.682 | – | +0.682 | $9.40 |

## Setup Generator

| Setup | Live | Trades | Sessions | Win | Break-even | Avg R | t | Last 4 R | P/L |
|---|---|---|---|---|---|---|---|---|---|
| GEN-261019-10-FlowShiftge0p42-SMA50dge1p7-PM-BRoplt0p5-t1s1-short | on | 4 | 1 | 75% | 60% | +0.276 | 0.59 | +0.276 | $97.24 |
| GEN-261019-03-Ret15mATRlem0p12-FromOpenATRlem0p34-SMA20slopege0p29-PM-BRoplt0p5-t05s1-long | on | 2 | 1 | 50% | 94% | -0.486 | -0.89 | -0.486 | $-57.96 |

MF4 backtest: Apr–Jun positive; 2-year −0.10R (swarm1017). MF1/MF3/MF5: negative on 2-year history after rework (swarm1017).

Educational only — not financial advice.
