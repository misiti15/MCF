### (a) Primary — record since current admission
| Setup | Account | Trades | Traded / active sessions | Total R | Avg R | Avg R w/o best day | Best-day share | Green days | Last-5 R | Fit / check avg | Corr to rest of Primary | Admitted | -10R demotion? |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Gap-Down Recovery Fade (all day) (`L3-gap-slope-fromopen-FD`) | Primary | 152 | 11/14 | +45.2 | +0.297 | +0.142 | 68% `1 day` | 55% | +39.4 | -0.021 / +0.351 | +0.39 | 2026-10-30 | no |
| Late-Day ETF Dip Buy (near-miss) (`NM-ETF-late-dip-di-long`) | Primary | 12 | 5/6 | +2.0 | +0.168 | +0.159 | 37% | 100% | +2.0 | +0.217 / +0.151 | n/a | 2026-11-11 | no |
| Big Loser Flush Buy (`NS5-sma50-flush-oversold-long`) | Primary | 41 | 17/29 | +0.1 | +0.003 | -0.050 | 1782% `1 day` | 53% | -1.1 | +0.142 / -0.086 | -0.03 | 2026-10-09 | no |
| Gap-Down Pop Fade, Heavy Selling (all day) (`RW3-gapdn-rsi5pop-flowsell-short-FD`) | Primary | 161 | 23/24 | +23.3 | +0.144 | -0.008 | 104% `1 day` | 48% | +1.9 | +0.441 / -0.001 | +0.60 | 2026-10-16 | no |
| Gap-Down Pop Fade (all day) (`RW5-heat30-flowsell-rsi5pop-gapdn-short-FD`) | Primary | 173 | 24/24 | +18.7 | +0.108 | -0.007 | 105% `1 day` | 58% | +10.6 | +0.327 / -0.045 | +0.53 | 2026-10-16 | no |
| RSI Collapse Dip Buy (all day) (`ST7-rsi50dn-long-pm-t1s1-FD`) | Primary | 34 | 12/16 | +2.0 | +0.060 | -0.044 | 155% `1 day` | 50% | -1.8 | +0.133 / -0.059 | -0.07 | 2026-10-28 | no |

### (b) On Deck — record outside Primary (dedup), C3-BAR2 as proposed
| Setup | Account | Trades | Traded / active sessions | Total R | Avg R | Avg R w/o best day | Best-day share | Green days | Last-5 R | Fit / check avg | Corr to Primary | C3-BAR2 fails | Since On Deck admission (n / R) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Gap-Down Bounce-off-Low Fade (all day) (`L3-gap-slope-lowdist-FD`) | On Deck | 109 | 19/28 | +27.4 | +0.252 | +0.120 | 66% `1 day` | 53% | +22.6 | +0.066 / +0.398 | +0.33 | best>=50% | 109 / +27.4 |
| Gap-Down Rebound Overbought Short (all day) (`L3-gap-slope-rsi5hi-FD`) | On Deck | 136 | 16/20 | +26.0 | +0.191 | +0.131 | 51% `1 day` | 69% | +12.8 | +0.196 / +0.188 | +0.28 | best>=50% | 60 / +12.8 |
| Gap-Down VWAP Loss Short (10% gap) (`CWT09-gapdn-vwaploss-g10-short`) | On Deck | 24 | 13/28 | +5.5 | +0.228 | +0.150 | 48% | 77% | +0.6 | +0.395 / +0.061 | -0.02 | n<30;shrunk<=0 | 8 / +0.2 |
| Big Gainer Dip-and-Pop (`NS1-rsidip-rsi5pop-long`) | On Deck | 7 | 3/7 | +1.1 | +0.159 | -0.116 | 142% `1 day` | 67% | +1.1 | n/a / n/a | n/a | n<30;sess<8;active<15;nonov w/o best<=0;best>=50%;shrunk<=0 | 4 / -0.5 |
| Panic Flush Reversal (5x volume) (`CWT05-flush-m05-v5-long`) | On Deck | 21 | 12/28 | +0.5 | +0.023 | -0.062 | 330% `1 day` | 50% | +1.8 | -0.328 / +0.286 | -0.61 | n<30;nonov w/o best<=0;best>=50%;shrunk<=0 | 7 / +0.4 |
| Gap-Down Bounce Rejection Short (10% gap) (`CWT09-gapdn-bounce-g10-lowerhalf-short`) | On Deck | 23 | 9/28 | +0.1 | +0.004 | -0.207 | 4407% `1 day` | 56% | +4.4 | -0.391 / +0.366 | -0.13 | n<30;nonov w/o best<=0;best>=50%;shrunk<=0 | 4 / -1.6 |
| Gap-Up Faller Volume Spike Short (all day) (`ST6-volspikeup-short-mid-t1s1-FD`) | On Deck | 47 | 11/28 | -0.5 | -0.011 | -0.098 | n/a (total ≤ 0) | 64% | -0.1 | +0.386 / -0.080 | +0.29 | nonov w/o best<=0;best>=50%;shrunk<=0 | 32 / -0.1 |
| Afternoon Higher-Low Long (near-miss) (`NM-HL-T75-pm-long`) | On Deck | 63 | 14/23 | -1.5 | -0.023 | -0.081 | n/a (total ≤ 0) | 57% | -0.4 | -0.099 / +0.139 | +0.12 | nonov w/o best<=0;best>=50%;shrunk<=0 | 9 / -0.8 |
| 20-Minute Opening Range Breakout (`orb20_a`) | On Deck | 38 | 18/28 | -1.5 | -0.040 | -0.194 | n/a (total ≤ 0) | 44% | +1.6 | -0.095 / +0.028 | +0.27 | nonov w/o best<=0;green<50%;best>=50%;shrunk<=0 | 38 / -1.5 |
| Early Sellers into a Pop (`MF3-open-flowsell-rsi5hi`) | On Deck | 43 | 8/23 | -3.7 | -0.086 | -0.193 | n/a (total ≤ 0) | 50% | -6.2 | -0.256 / +0.352 | +0.67 | nonov w/o best<=0;best>=50%;shrunk<=0 | 40 / -2.0 |
| Gap-Down Bounce Short, Heavy Selling (all day) (`RW1-gapdn-bounce-flowsell-short-FD`) | On Deck | 219 | 27/28 | -6.0 | -0.028 | -0.056 | n/a (total ≤ 0) | 52% | -10.8 | +0.070 / -0.078 | +0.45 | nonov w/o best<=0;best>=50%;shrunk<=0 | 98 / -10.8 |
| Early Sellers, Strong Heat (all day) (`MF4-h40-open-flowsell-FD`) | On Deck | 95 | 13/13 | -8.9 | -0.093 | -0.159 | n/a (total ≤ 0) | 54% | -13.0 | +0.289 / -0.223 | +0.15 | active<15;nonov w/o best<=0;best>=50%;shrunk<=0 | 63 / -17.6 |
| Early Sellers, Mid-High RSI (all day) (`MF2-open-rsimidhi-flowsell-FD`) | On Deck | 76 | 11/13 | -27.3 | -0.360 | -0.482 | n/a (total ≤ 0) | 27% | -35.7 | +0.277 / -0.603 | +0.07 | active<15;nonov w/o best<=0;green<50%;best>=50%;shrunk<=0 | 53 / -35.7 |

### (c) Arena → On Deck — closest to C3-BAR2 (n ≥ 10 and avg R w/o best day > 0, or total > +5R with t ≥ 1.5)
| Setup | Account | Trades | Traded / active sessions | Total R | Avg R | Avg R w/o best day | Best-day share | Green days | Last-5 R | Fit / check avg | Corr to Primary | C3-BAR2 fails | t |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Generated: Late-AM Divergence Short (quiet) (`GEN-261021-01-BearDiv-RVolDayle0p47-BarsSinceHODle0-LAM-SPYltm0p25-t1s1-short`) | Testing E (guest) | 15 | 2/21 | +5.0 | +0.335 | +0.561 | 89% `1 day` | 100% | +5.0 | n/a / n/a | n/a | n<30;sess<8;best>=50%;shrunk<=0 | +1.57 |
| Generated: Lunch New-Low Short (selling) (`GEN-261026-03-NewLOD-Flow3lem0p37-FromOpenATRlem0p78-LUNCH-BRopgt0p5-holdtr-short`) | Testing D | 25 | 6/18 | +11.3 | +0.454 | +0.288 | 54% `1 day` | 83% | +10.3 | +0.509 / +0.403 | n/a | n<30;sess<8;best>=50%;shrunk<=0 | +1.95 |
| Generated: Late Pullback Buy (MACD rising) (`GEN-261027-01-MACDhge0p12-Ret15mATRlem0p069-LATE-BRvwgt0p5-t05s1-long`) | Testing E | 17 | 7/17 | +3.4 | +0.201 | +0.160 | 35% | 86% | +1.9 | +0.164 / +0.254 | n/a | n<30;sess<8;shrunk<=0 | +1.54 |
| Generated: PM Lower-Band Dip Buy (uptrend) (`GEN-261019-02-BBpctle0p017-SMA20slopege0p46-PM-QQQdn-t05s1-long`) | Testing F | 13 | 7/23 | +3.0 | +0.231 | +0.142 | 53% `1 day` | 71% | +3.1 | -0.247 / +0.443 | n/a | n<30;sess<8;best>=50%;shrunk<=0 | +1.30 |
| Early NS3 Short While QQQ Up (near-miss) (`NM-RWR3-ns3-qqqup-early-short`) | Testing C | 11 | 6/23 | +4.5 | +0.410 | +0.133 | 76% `1 day` | 50% | +4.8 | -0.155 / +0.733 | n/a | n<30;sess<8;best>=50%;shrunk<=0 | +1.33 |
| Generated: Lunch Failed-Breakdown Short (`GEN-261027-08-ORBfailDn-FromPCATRlem0p96-LUNCH-QQQltm0p6-hold-short`) | Testing B | 78 | 6/17 | +8.7 | +0.112 | +0.030 | 79% `1 day` | 50% | +5.1 | +0.170 / +0.047 | n/a | sess<8;best>=50%;shrunk<=0 | +1.17 |
| NS2 Short, SPY Up 0.5%, Not Friday (near-miss) (`NM-RWN4-ns2-spyup05-notfri-short`) | Testing F | 40 | 2/23 | +9.1 | +0.228 | -0.043 | 104% `1 day` | 50% | +9.1 | n/a / n/a | n/a | sess<8;nonov w/o best<=0;best>=50%;shrunk<=0 | +3.23 |
| Generated: Midday Stretched Dip Buy (`GEN-261020-09-EMAdChgge0p093-Z12lem0p82-VWAPcrossesle0-MID-QQQltm0p3-holdtr-long`) | Setup Generator | 189 | 7/22 | +61.3 | +0.324 | -0.100 | 118% `1 day` | 43% | +68.5 | +0.015 / +0.519 | n/a | sess<8;nonov w/o best<=0;green<50%;best>=50% | +4.67 |
| Failed Opening-Range-Low Break Long (`CWT14-failbrk-orl-p10-long-WB5`) | Testing D | 75 | 2/2 | +7.7 | +0.103 | -0.199 | 110% `1 day` | 50% | +7.7 | n/a / n/a | n/a | sess<8;active<15;nonov w/o best<=0;best>=50%;shrunk<=0 | +1.96 |

### (d) Arena → Graveyard — meets C3-EXIT100 (≥ 100 trades, ≥ 15 active days, avg ≤ −0.05, w/o best day ≤ 0)
| Setup | Account | Trades | Traded / active sessions | Total R | Avg R | Avg R w/o best day | Best-day share | Green days | Last-5 R | Fit / check avg | Corr to Primary | Current account n / avg |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Generated: Morning Strong-Trend Drop Short (`GEN-261022-09-Ret15mATRlem0p16-BarRngATRge0p11-ADX7ge64-AM-BRvwlt0p3-hold-short`) | Setup Generator | 211 | 3/20 | -181.8 | -0.862 | -0.882 | n/a (total ≤ 0) | 0% | -181.8 | n/a / n/a | n/a | 211 / -0.862 |
| Failed Prior-Day-Low Break Long (`CWT14-failbrk-pdl-p10-long`) | Testing A | 870 | 28/28 | -105.3 | -0.121 | -0.143 | n/a (total ≤ 0) | 43% | -54.4 | -0.023 / -0.198 | -0.15 | 870 / -0.121 |
| Generated: Morning Overbought Drop Short (`GEN-261029-08-Ret15mlem0p36-Flow3lem0p54-RSI14ge65-AM-SPYgt0p5-hold-short`) | Setup Generator | 169 | 6/15 | -61.7 | -0.365 | -0.766 | n/a (total ≤ 0) | 50% | -61.8 | -0.193 / -0.721 | n/a | 169 / -0.365 |
| Generated: Open Prior-Day-Low Buy (SPY down) (`GEN-261019-05-RSIslopelem9-PDLdistle0p14-EMAdifflem0p46-OPEN-SPYltm0p5-t1s1-long`) | Testing D | 103 | 4/23 | -57.2 | -0.555 | -0.617 | n/a (total ≤ 0) | 0% | -57.2 | -1.004 / -0.080 | n/a | 11 / -0.040 |
| Failed Prior-Day-Low Break Long (0.1 ATR, low volume) [fill] (`CWT14-failbrk-pdl-p10-lowvol-long`) | Testing D | 436 | 23/23 | -43.5 | -0.100 | -0.134 | n/a (total ≤ 0) | 35% | -21.6 | -0.050 / -0.128 | +0.01 | 196 / -0.110 |
| Generated: Morning RSI Surge Buy (`GEN-261020-07-RSIslopege19-LowWickge0p33-ATRdge4p4-AM-BRvwgt0p7-hold-long`) | Testing E | 129 | 7/22 | -42.3 | -0.328 | -0.505 | n/a (total ≤ 0) | 29% | -49.1 | -0.549 / -0.096 | n/a | 3 / -1.100 |
| Generated: Midday Gap-Up Failed-Break Buy (`GEN-261021-06-ORBfailUp-Gapge1p2-MID-BRopgt0p5-hold-long`) | Setup Generator | 237 | 11/21 | -41.6 | -0.175 | -0.258 | n/a (total ≤ 0) | 55% | +6.4 | -0.322 / -0.023 | +0.16 | 237 / -0.175 |
| Stretched Below VWAP Bounce (`CWT13-vwapstretch-z05-long`) | Testing A | 334 | 24/27 | -31.5 | -0.094 | -0.125 | n/a (total ≤ 0) | 54% | +4.4 | -0.034 / -0.127 | +0.14 | 281 / -0.129 |
| Generated: Morning Selling-Burst Buy (`GEN-261028-09-FlowShiftlem0p65-ADX7le23-AM-BRoplt0p35-t05s1-long`) | Testing E | 136 | 7/16 | -30.7 | -0.226 | -0.251 | n/a (total ≤ 0) | 14% | -14.7 | -0.341 / -0.152 | n/a | 40 / -0.284 |
| Generated: Morning VWAP Reclaim Buy (SPY up) (`GEN-261021-07-VWAPxUp-ORBfailUp-AM-SPYgt0p5-hold-long`) | Setup Generator | 143 | 6/21 | -27.6 | -0.193 | -0.339 | n/a (total ≤ 0) | 33% | -42.4 | -0.252 / -0.130 | n/a | 143 / -0.193 |
| Generated: Lunch Tight-Range Pop Buy (`GEN-261028-08-Ret5mge0p21-SMA20dlem0p16-Compress6le0p11-LUNCH-BRoplt0p35-holdtr-long`) | Testing B | 132 | 5/16 | -27.2 | -0.206 | -0.230 | n/a (total ≤ 0) | 20% | -27.2 | -0.262 / -0.169 | n/a | 67 / -0.205 |
| Generated: Midday Volume Buy (volatile) (`GEN-261027-05-VolRatioge1p5-ORLdistge0p41-ATRdge6-MID-BRvwgt0p7-t05s1-long`) | Testing C | 107 | 5/17 | -23.5 | -0.219 | -0.281 | n/a (total ≤ 0) | 40% | -23.5 | -0.228 / -0.216 | n/a | 31 / -0.116 |
| Generated: Morning Failed-Break Buy (wild) (`GEN-261022-01-ORBfailUp-ATRdge7p9-Eff6ge0p55-AM-SPYdn-hold-long`) | Setup Generator | 161 | 12/20 | -19.6 | -0.121 | -0.266 | n/a (total ≤ 0) | 33% | -3.2 | -0.137 / -0.116 | +0.32 | 161 / -0.121 |
| Generated: Lunch Failed Breakdown Buy (`GEN-261020-05-ORBfailDn-VWAPcrossesge4-SMA20dlem0p31-LUNCH-SPYgt0p25-holdtr-long`) | Testing F | 123 | 9/22 | -19.4 | -0.158 | -0.203 | n/a (total ≤ 0) | 56% | -17.2 | -0.050 / -0.218 | -0.86 | 37 / -0.651 |
| Big Gainer Dip-and-Pop (all day) (`NS1-rsidip-rsi5pop-long-FD`) | Testing E | 109 | 24/28 | -17.8 | -0.163 | -0.245 | n/a (total ≤ 0) | 42% | -11.1 | -0.081 / -0.211 | -0.09 | 16 / -0.554 |
| Afternoon Blow-off Short (all day) (`exhaustion_short-FD`) | Testing A | 248 | 26/28 | -12.7 | -0.051 | -0.102 | n/a (total ≤ 0) | 46% | -8.5 | -0.025 / -0.082 | -0.24 | 62 / -0.137 |
| Generated: Morning VWAP-Loss Low Buy (QQQ up) (`GEN-261028-02-VWAPxDn-NewLOD-AM-QQQgt0p6-t1s1-long`) | Setup Generator | 131 | 6/16 | -8.8 | -0.067 | -0.174 | n/a (total ≤ 0) | 50% | -5.6 | -0.147 / -0.042 | n/a | 131 / -0.067 |
| Sellers into Strength (all day) (`MF5-flowsell-vwapup-rsi5hi`) | Testing A | 114 | 22/23 | -7.9 | -0.069 | -0.152 | n/a (total ≤ 0) | 50% | +8.0 | -0.108 / -0.039 | +0.22 | 31 / +0.258 |

EXIT100 total: 18 setups, 3893 trades, -760.0R.

### (d2) Not yet EXIT100 (n 50-99 or < 15 active days) but on the same path — watch, no proposal
| Setup | Account | Trades | Traded / active sessions | Total R | Avg R | Avg R w/o best day | Best-day share | Green days | Last-5 R | Fit / check avg | Corr to Primary |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Generated: Open Up-Day Bounce Short (`GEN-261026-05-Ret15mATRge0p042-FromPCATRge0p28-ORHdistlem0p38-OPEN-BRopgt0p5-hold-short`) | Testing E | 68 | 7/18 | -61.8 | -0.909 | -0.951 | n/a (total ≤ 0) | 43% | -47.5 | -0.656 / -1.008 | n/a |
| Generated: Midday Low Bounce Buy (MACD up) (`GEN-261020-03-MACDhge0p079-BarsSinceLODle5-MID-BRvwlt0p3-t05s05-long`) | Testing B | 61 | 5/22 | -46.3 | -0.759 | -0.781 | n/a (total ≤ 0) | 0% | -46.3 | -0.727 / -0.945 | n/a |
| Failed Prior-Day-Low Break, SPY-Range Regime (long leg) (`CWT14-failbrk-pdl-p05-R2A-long`) | Testing A | 366 | 8/13 | -39.7 | -0.108 | -0.116 | n/a (total ≤ 0) | 12% | -28.1 | -0.110 / -0.108 | -0.35 |
| Generated: PM Upper-Wick Short (weak mkt) (`GEN-261022-05-MACDhge0p079-UpWickge0p71-ORHdistlem0p38-PM-BRoplt0p35-holdtr-short`) | Testing B | 88 | 5/20 | -29.5 | -0.335 | -0.402 | n/a (total ≤ 0) | 40% | -29.5 | -0.585 / -0.021 | n/a |
| Generated: Morning Weak-Bounce Short (quiet) (`GEN-261022-08-EMAdChglem0p094-Flow3ge1-RVolDayle0p59-AM-SPYgt0p25-holdtr-short`) | Testing E | 92 | 8/20 | -24.5 | -0.266 | -0.503 | n/a (total ≤ 0) | 25% | -21.3 | -0.109 / -0.500 | +0.30 |
| Gap-Down Capitulation Buy (near-miss) (`NM-AR-AM-gapdown-capitulation-long`) | Testing A | 74 | 14/23 | -21.1 | -0.285 | -0.361 | n/a (total ≤ 0) | 36% | +5.6 | -0.398 / -0.050 | -0.32 |
| Generated: Lunch Choppy RSI Turn Buy (`GEN-261023-07-RSIslopege9p1-BarRngATRge0p087-VWAPcrossesge8-LUNCH-BRvwgt0p7-hold-long`) | Testing A | 53 | 7/19 | -20.5 | -0.386 | -0.503 | n/a (total ≤ 0) | 43% | -22.0 | +0.034 / -0.461 | n/a |
| Index Last-Half-Hour Momentum (`intraday_momentum`) | Testing F | 69 | 26/28 | -19.3 | -0.279 | -0.300 | n/a (total ≤ 0) | 31% | -0.5 | -0.196 / -0.333 | +0.34 |
| Generated: Morning Up-Stock Dip Short (`GEN-261027-07-RSI14le35-FromOpenge2-AM-BRvwlt0p5-t1s1-short`) | Testing E | 55 | 9/17 | -16.1 | -0.292 | -0.442 | n/a (total ≤ 0) | 67% | -21.2 | +0.462 / -0.481 | -0.56 |
| Generated: PM Oversold Turn Buy (MACD rising) (`GEN-261020-01-MACDhge0p12-RSI5le25-PM-BRvwgt0p6-t1s05-long`) | Setup Generator | 55 | 6/22 | -15.9 | -0.289 | -0.305 | n/a (total ≤ 0) | 17% | -12.4 | -0.597 / -0.259 | n/a |
| Generated: PM Gap-Up Dip Buy (MACD falling) (`GEN-261029-03-MACDhlem0p12-Ret5mlem0p062-Gapge2-PM-QQQup-hold-long`) | Testing B | 64 | 7/15 | -15.7 | -0.245 | -0.282 | n/a (total ≤ 0) | 43% | -13.8 | -0.014 / -0.449 | n/a |
| Generated: Late-AM New-Low Buy (SPY up) (`GEN-261027-03-NewLOD-DayPosle0p19-SMA20dlem0p59-LAM-SPYgt0p5-hold-long`) | Testing D | 50 | 5/17 | -15.7 | -0.313 | -0.427 | n/a (total ≤ 0) | 40% | -15.7 | +1.244 / -0.413 | n/a |
| Big Loser VWAP Reclaim Fade (`NS3-failed-vwap-reclaim-short`) | Testing E | 80 | 15/26 | -15.6 | -0.196 | -0.324 | n/a (total ≤ 0) | 33% | +0.4 | -0.168 / -0.234 | +0.26 |
| Generated: Midday Choppy Oversold Buy (`GEN-261029-02-RSI2le0-VWAPcrossesge9-DayRngVsPrevle0p52-MID-BRvwlt0p4-hold-long`) | Testing B | 60 | 10/15 | -14.7 | -0.244 | -0.297 | n/a (total ≤ 0) | 40% | -7.4 | -0.226 / -0.266 | -0.25 |
| Big Loser VWAP Reclaim Fade, Morning, Wide Stop (`NS3V1-am-widestop-short`) | Testing A | 82 | 12/19 | -14.2 | -0.173 | -0.240 | n/a (total ≤ 0) | 33% | -0.8 | -0.276 / -0.065 | -0.04 |
| Generated: Midday Failed-Breakout Low Buy (`GEN-261027-06-ORBfailUp-BarsSinceLODle5-MID-BRoplt0p35-holdtr-long`) | Testing C | 85 | 7/17 | -13.5 | -0.159 | -0.386 | n/a (total ≤ 0) | 43% | -10.8 | -0.347 / -0.040 | n/a |
| Panic Flush Reversal (3x volume) (`CWT05-flush-m05-v3-long`) | Testing F | 89 | 20/28 | -10.5 | -0.117 | -0.165 | n/a (total ≤ 0) | 50% | +0.1 | -0.051 / -0.161 | -0.23 |
| Failed Prior-Day-Low Break, SPY-Range Regime (short leg) (`CWT14-failbrk-pdl-p05-R2A-short`) | Testing A | 138 | 5/13 | -7.9 | -0.057 | -0.057 | n/a (total ≤ 0) | 0% | -7.9 | -0.165 / -0.037 | n/a |
| Generated: PM Gap-Down Above-VWAP Short (`GEN-261027-04-VWAPatrge0-Gaplem2-FromOpenlem2-PM-SPYdn-t1s1-short`) | Testing C | 60 | 8/17 | -6.0 | -0.101 | -0.287 | n/a (total ≤ 0) | 38% | -8.8 | +0.099 / -0.208 | +0.24 |
| Generated: Late New-Low Buy (SPY down) (`GEN-261026-06-NewLOD-SMA20slopelem0p28-LATE-SPYltm0p25-t1s1-long`) | Testing C | 59 | 6/18 | -4.8 | -0.081 | -0.326 | n/a (total ≤ 0) | 50% | -15.0 | +0.045 / -0.264 | n/a |

### (e) Graveyard → arena (GY-LIFE graduation: ≥ 15 Graveyard days, ≥ 30 Graveyard trades, whole w/o best day > 0, best day < 50%)
| Setup | Status | Whole n / sessions | Whole avg R | Whole w/o best | Whole best share | GY n / days | GY avg R | GY w/o best | GY best share | GY last-5 R | Corr to Primary | Graduates? |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Big Gainer Fade, VWAP Band Guard (all day) (`RW6G1-ns2-up3-vwap2sd-short-FD`) | active | 67 / 22 | +0.020 | -0.055 | 297% `1 day` | 37 / 9 | +0.171 | +0.120 | 64% `1 day` | +3.5 | +0.26 | no |
| EMA Cross-Down Dip Buy (all day) (`ST4-emadn-long-am-t1s05-FD`) | off (in arena) | 56 / 18 | +0.028 | -0.110 | 406% `1 day` | 23 / 6 | +0.293 | +0.027 | 96% `1 day` | +5.8 | -0.41 | no |
| Midday Gap-Up Dip Buy (`heat_fade_long`) | active | 275 / 29 | -0.128 | -0.190 | n/a (total ≤ 0) | 137 / 18 | +0.093 | +0.012 | 90% `1 day` | +15.2 | +0.02 | no |
| Big Gainer SMA50 Cross Fade (all day) (`RW6-ns2-up3-short-FD`) | off (in arena) | 197 / 25 | +0.069 | -0.203 | 281% `1 day` | 144 / 15 | +0.268 | +0.008 | 99% `1 day` | +39.3 | +0.45 | no |
| Gap-Down Heavy-Selling Short, no RSI condition (all day) (`RW3S-gapdn-flowsell-short-FD`) | active | 428 / 12 | -0.199 | -0.232 | n/a (total ≤ 0) | 131 / 3 | +0.007 | -0.075 | 957% `1 day` | +0.9 | +0.30 | no |
| Failed Opening-Range-Low Break Long (low volume) (`CWT14-failbrk-orl-p10-lowvol-long`) | benched 11-18..11-24 | 816 / 27 | -0.086 | -0.113 | n/a (total ≤ 0) | 639 / 20 | -0.061 | -0.093 | n/a (total ≤ 0) | -21.9 | -0.12 | no |
| Stretched Above VWAP Fade (`CWT13-vwapstretch-z05-short`) | active | 206 / 24 | -0.155 | -0.192 | n/a (total ≤ 0) | 145 / 17 | -0.051 | -0.095 | n/a (total ≤ 0) | -2.7 | +0.02 | no |
| Gap-Down Bounce Rejection Short (5% gap) (`CWT09-gapdn-bounce-g5-lowerhalf-short`) | active | 200 / 22 | -0.148 | -0.208 | n/a (total ≤ 0) | 158 / 18 | -0.028 | -0.104 | n/a (total ≤ 0) | -24.1 | -0.01 | no |
| Failed Opening-Range-Low Break Long (0.05 ATR) [fill] (`CWT14-failbrk-orl-p05-long`) | benched 11-18..11-24 | 1390 / 27 | -0.104 | -0.130 | n/a (total ≤ 0) | 1027 / 20 | -0.081 | -0.114 | n/a (total ≤ 0) | -28.3 | -0.50 | no |
| Big Gainer Average Reclaim Fade (all day) (`NS2-sma50break-overbought-short-FD`) | benched 11-18..11-24 | 285 / 26 | -0.028 | -0.233 | n/a (total ≤ 0) | 216 / 19 | +0.116 | -0.114 | 165% `1 day` | +44.4 | +0.49 | no |
| Failed Opening-Range-Low Break Long (0.1 ATR) [fill] (`CWT14-failbrk-orl-p10-long`) | benched 11-18..11-24 | 811 / 27 | -0.125 | -0.147 | n/a (total ≤ 0) | 618 / 20 | -0.102 | -0.131 | n/a (total ≤ 0) | -27.4 | -0.10 | no |
| Failed Opening-Range-Low Break Long (0.05 ATR, low volume) [fill] (`CWT14-failbrk-orl-p05-lowvol-long`) | benched 11-18..11-24 | 1305 / 27 | -0.144 | -0.180 | n/a (total ≤ 0) | 954 / 20 | -0.099 | -0.144 | n/a (total ≤ 0) | -65.0 | -0.37 | no |
| Down-Stock Trend-Turn Buy (all day) (`ST2-slope20up-long-am-t05s1-FD`) | benched 11-18..11-24 | 348 / 25 | -0.103 | -0.166 | n/a (total ≤ 0) | 267 / 19 | -0.067 | -0.145 | n/a (total ≤ 0) | +12.3 | -0.17 | no |
| Sellers into Strength (full-day copy) (`MF5-flowsell-vwapup-rsi5hi-FD`) | active | 180 / 27 | -0.171 | -0.218 | n/a (total ≤ 0) | 98 / 12 | -0.069 | -0.149 | n/a (total ≤ 0) | +14.1 | +0.34 | no |
| Early Sellers into a Pop (all day) (`MF3-open-flowsell-rsi5hi-FD`) | active | 305 / 28 | -0.152 | -0.191 | n/a (total ≤ 0) | 162 / 12 | -0.080 | -0.150 | n/a (total ≤ 0) | +10.6 | +0.33 | no |
| Opening-Range Breakdown Buy (all day) (`ST1-ordn-long-pm-t05s1-FD`) | active | 73 / 20 | -0.200 | -0.315 | n/a (total ≤ 0) | 49 / 15 | -0.018 | -0.152 | n/a (total ≤ 0) | +2.3 | -0.08 | no |
| Failed Prior-Day-High Break Short (0.05 ATR, low volume) [fill] (`CWT14-failbrk-pdh-p05-lowvol-short`) | benched 11-18..11-24 | 649 / 27 | -0.152 | -0.168 | n/a (total ≤ 0) | 417 / 19 | -0.141 | -0.166 | n/a (total ≤ 0) | -18.1 | +0.12 | no |
| Big Gainer Average Reclaim Fade (`NS2-sma50break-overbought-short`) | active | 72 / 10 | -0.358 | -0.395 | n/a (total ≤ 0) | 13 / 4 | -0.018 | -0.187 | n/a (total ≤ 0) | -0.2 | n/a | no |
| Morning Bounce Fade (all day) (`heat_fade_short-FD`) | benched 11-18..11-24 | 848 / 26 | -0.100 | -0.141 | n/a (total ≤ 0) | 496 / 19 | -0.120 | -0.194 | n/a (total ≤ 0) | -37.0 | +0.44 | no |
| Failed Prior-Day-High Break Short (low volume) (`CWT14-failbrk-pdh-p10-lowvol-short`) | benched 11-18..11-24 | 315 / 26 | -0.183 | -0.208 | n/a (total ≤ 0) | 213 / 19 | -0.177 | -0.200 | n/a (total ≤ 0) | -13.1 | +0.06 | no |
| Coil Under the High (4 bars) (`CWT12-coil-k4-long`) | benched 11-18..11-24 | 972 / 27 | -0.135 | -0.153 | n/a (total ≤ 0) | 545 / 14 | -0.169 | -0.205 | n/a (total ≤ 0) | -80.9 | -0.26 | no |
| Failed Prior-Day-High Break Short (0.1 ATR) [fill] (`CWT14-failbrk-pdh-p10-short`) | benched 11-18..11-24 | 602 / 27 | -0.165 | -0.194 | n/a (total ≤ 0) | 369 / 18 | -0.181 | -0.213 | n/a (total ≤ 0) | -9.9 | +0.03 | no |
| Big Loser Flush Buy (all day) (`NS5-sma50-flush-oversold-long-FD`) | active | 93 / 26 | -0.212 | -0.311 | n/a (total ≤ 0) | 47 / 10 | -0.050 | -0.220 | n/a (total ≤ 0) | +1.3 | +0.12 | no |
| Big-Stock VWAP Reclaim Fade (all day) (`RW4-ns3-adv150-short-FD`) | active | 212 / 25 | -0.191 | -0.232 | n/a (total ≤ 0) | 108 / 11 | -0.138 | -0.232 | n/a (total ≤ 0) | -8.8 | -0.02 | no |
| Coil Under the High (6 bars) (`CWT12-coil-k6-long`) | benched 11-18..11-24 | 271 / 24 | -0.181 | -0.259 | n/a (total ≤ 0) | 181 / 15 | -0.136 | -0.251 | n/a (total ≤ 0) | -19.0 | -0.35 | no |
| Failed Prior-Day-Low Break Long (0.05 ATR, low volume) [fill] (`CWT14-failbrk-pdl-p05-lowvol-long`) | benched 11-18..11-24 | 765 / 27 | -0.147 | -0.171 | n/a (total ≤ 0) | 332 / 13 | -0.189 | -0.255 | n/a (total ≤ 0) | -35.9 | +0.02 | no |
| Big Loser VWAP Reclaim Fade (all day) (`NS3-failed-vwap-reclaim-short-FD`) | active | 264 / 24 | -0.153 | -0.199 | n/a (total ≤ 0) | 152 / 11 | -0.158 | -0.258 | n/a (total ≤ 0) | -14.3 | +0.15 | no |
| Early Sellers Above VWAP (all day) (`MF1-945-flowsell-vwapup-FD`) | active | 153 / 28 | -0.229 | -0.291 | n/a (total ≤ 0) | 113 / 21 | -0.188 | -0.271 | n/a (total ≤ 0) | +0.2 | +0.29 | no |
| Failed Prior-Day-Low Break Long (shallow) (`CWT14-failbrk-pdl-p05-long`) | benched 11-18..11-24 | 1077 / 27 | -0.146 | -0.167 | n/a (total ≤ 0) | 402 / 13 | -0.248 | -0.299 | n/a (total ≤ 0) | -90.0 | -0.22 | no |
| Opening-Range Low Sweep Reversal (`LIQ-orl-sweep-open15-s25-long`) | benched 11-18..11-24 | 393 / 26 | -0.174 | -0.226 | n/a (total ≤ 0) | 248 / 20 | -0.214 | -0.304 | n/a (total ≤ 0) | -41.4 | -0.53 | no |
| Morning Bounce Fade (`heat_fade_short`) | benched 11-18..11-24 | 395 / 28 | -0.206 | -0.290 | n/a (total ≤ 0) | 254 / 18 | -0.189 | -0.324 | n/a (total ≤ 0) | -15.5 | +0.16 | no |
| Big-Stock Blow-off Short (all day) (`RW2-exhaustion-noon-adv150-short-FD`) | benched 11-18..11-24 | 472 / 27 | -0.245 | -0.285 | n/a (total ≤ 0) | 321 / 20 | -0.285 | -0.351 | n/a (total ≤ 0) | -2.1 | -0.07 | no |
| Midday Gap-Up Dip Buy (all day) (`heat_fade_long-FD`) | benched 11-18..11-24 | 315 / 27 | -0.369 | -0.412 | n/a (total ≤ 0) | 165 / 20 | -0.349 | -0.397 | n/a (total ≤ 0) | -36.6 | +0.06 | no |
| Gap-Down VWAP Loss Short (5% gap) (`CWT09-gapdn-vwaploss-g5-short`) | active | 182 / 20 | -0.354 | -0.587 | n/a (total ≤ 0) | 149 / 14 | -0.277 | -0.557 | n/a (total ≤ 0) | -65.1 | -0.26 | no |
