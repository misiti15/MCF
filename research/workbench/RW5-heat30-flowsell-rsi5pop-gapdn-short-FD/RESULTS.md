# Workbench RESULTS — Gap-Down Pop Fade (all day) `RW5-heat30-flowsell-rsi5pop-gapdn-short-FD` (Primary, TEAM-6) vs its copies
Educational only — not financial advice. Mechanic 2026-11-16, built ~13:10-15:10 ET (market hours: research files only; no config change, no deploy).

## Verdict — supervisor sign-off
> **Recommended: `RW5-heat30-flowsell-rsi5pop-gapdn-short-FD-WB3`** — parent + three layers: skip when SPY is up more than
> +0.20% since the 09:50 bar close (market-state gate measured after 09:50, owner rule), stop-exit cost <= 15% of 1R
> (no thin-R names), entries from the 10:15 bar. **PASS — better than the parent in both tests on avg R, avg R w/o best day
> and worst day, and positive after costs in both.**

| copy | change | replay avg R (parent +0.117) | 2-year avg R (parent −0.031) | w/o best day (replay / 2y; parent +0.036 / −0.037) | worst day (replay / 2y; parent −13.4 / −25.3R) | trades (replay / 2y; parent 205 / 4,633) | verdict |
|---|---|---|---|---|---|---|---|
| WB1 | NEW gate: skip SPY > +0.30% since 09:50 | **+0.184** | **−0.007** | +0.088 / −0.014 | −12.5 / −25.3 | 156 / 3,670 | PASS (contained in WB3) |
| WB2 | P20/intake: stop-exit cost <= 0.15 of 1R | +0.122 | −0.022 | +0.034 / −0.028 | −10.3 / −15.9 | 145 / 3,570 | PASS (contained in WB3) |
| **WB3** | gate SPY <= +0.20% since 09:50 + cost/R <= 0.15 + start 10:15 | **+0.191** | **+0.017** | **+0.072 / +0.009** | **−10.3 / −15.9** | 100 / 2,435 | **PASS — recommended** |

Supervisor sign-off (what changed, why, before/after, where it gives back):
- **What / why.** The parent's losses come mainly from shorting gap-down pops while the index rallies after 09:50 (live: 67
  trades taken with SPY > +0.20% since 09:50 lost −9.2R; the other 118 made +32.4R). WB3 adds that gate, drops thin-R names
  whose stop cost eats > 15% of 1R (2-year worst day −25.3 → −15.9R) and skips the first 25 minutes.
- **Overall before → after (identical pipeline, LR8 costs):** replay +0.117 → **+0.191R** (w/o best day +0.036 → +0.072);
  2-year −0.031 → **+0.017R** (−143R → +42R total; w/o best day −0.037 → +0.009); better in every 2-year split (TRAIN
  −0.047 → −0.011, VALID −0.035 → +0.021, FWD +0.129 → +0.221). Paired-by-day t vs parent: 2-year +2.51 (dR +188R),
  replay −0.24.
- **Where it gives back:** (1) fewer trades — about half (replay 205 → 100, 2-year −47%), so the replay TOTAL is lower
  (+24.0R → +19.1R, dR −4.9R) even though every trade is better on average; (2) up-market days stay negative (2-year up-day
  −0.286 → −0.225R on 516 trades) and a day like 11-10 (SPY not up after 09:50, still −12.5R live) is only partly avoided;
  (3) two of the five best live trades (VFLO, KMI on 11-03) would not be taken (cost/R 0.35 / 0.20; VFLO also SPY +0.29%).
- **Honest limits:** no copy clears the configs-counted bar max(1.5, sqrt(2 ln 38)) = 2.70 (WB3 2-year t 2.51 — close, not
  over; under the owner's 2026-11-16 clarified rule the t is reported, not used to pass). The gate threshold 0.20 was chosen
  after S1 (0.20) scored next to V23 (0.30); 0.30 (WB1) is the pre-declared one and passes too. The replay is the parent's
  live signal symbol-days, so the ADV part (P2) could not be replayed.

## Method (identical for parent and every copy) — reused harness from research/workbench/L3-gap-slope-fromopen-FD/code
- **Replay of the live sessions (backtest, not live results):** every symbol-day on which the parent signalled live in any
  account and was shortable+ETB, 2026-10-12..11-13 (233 symbol-days, 24 sessions). 1-min SIP bars (read-only GET) → lab
  frame (`mcf.report.engine.lab_frame` + daily priors as live). Parent replay 205 trades +0.117R vs live 185 trades +0.125R.
- **2-year backtest:** lab frames 2024-10..2026-11-04, **locked block 2024-11-01..2025-02-28 never read** (asserted in
  cand2y.py / paths2y.py / load.py), ADV >= $95M, names shortable+ETB on >= 90% of the universe snapshots (E90 proxy, same
  file as the L3 jobs). Splits TRAIN <= 2025-12-31, VALID 2026-01..10-05, FWD 10-06..11-04.
- Same engine for both: RW5 sensors on 5-min bar close (heat <= −30, buyPressure < −0.15, RSI(5) > 80, gap < 0), refire off
  (first qualifying bar per symbol-day, as Primary runs it), entry at the signal-bar close, price >= $5, exits on 1-min bars
  (stop first; target only when traded through by $0.01; flat 15:55), **LR8 costs**, Primary's book (<= 30 lots, <= 3 per
  symbol, −2R latch). SPY-since-09:50 from SPY 1-min closes (09:50 bar close reference). The parent's live record is NOT used
  in the pass decision.
- Module parity (WB modules vs bench mask on the replay frames): WB1 249/252, WB2 234/234, WB3 164/167 bar hits; the 3
  misses are one symbol-day (SYRE 11-10) with no 09:50 5-min bar, where the module fails safe (no signal).
- Rule changes inside the replay window (ledger): 10-15 promotion, 10-20 twin rule / Testing -2R, 10-21 promotion = move,
  10-28 Primary size / cap 30, 10-29 Primary −2R latch, 10-30 Testing CF, 11-12 LR1/LR3/LR5/LR7 + LR8 costs. The replay
  applies today's rules to every session, so none of these mixes into the comparison.

## Every configuration tried (38), including failures
Round 1 (V01-V24, one part each, pre-declared in code/decl.py before any 2-year score; V08 dropped before running), Round 2
(S1/S2 thresholds and combos C1-C10, declared after Round 1), Round 3 (D1-D3, declared after Round 2). Pass rule (owner
2026-11-16): meets or exceeds the parent's avg R in BOTH tests (meets = within 0.01R or >= 95%), and not worse on avg R w/o
best day by > 0.02R or on worst day by > 10%.

| copy | config | replay n | replay avg R | replay w/o best day | replay worst day | 2y n | 2y avg R | 2y w/o best day | 2y worst day | t vs parent (replay / 2y) | verdict |
|---|---|---|---|---|---|---|---|---|---|---|---|
| parent | PARENT | 205 | +0.117 | +0.036 | -13.4 | 4633 | -0.031 | -0.037 | -25.3 | +0.00 / +0.00 | — |
|  | V01 ADV >= $150M (P2) | 205 | +0.117 | +0.036 | -13.4 | 3432 | -0.054 | -0.061 | -19.0 | +0.00 / -0.82 | FAIL — 2y avg R -0.054 < parent -0.031; 2y w/o best day -0.061 vs -0.037 |
|  | V02 price >= $10 (P3) | 196 | +0.142 | +0.050 | -13.4 | 4588 | -0.032 | -0.038 | -25.3 | +1.70 / -0.39 | PASS |
|  | V03 window end 15:00->13:00 (P6) | 155 | +0.165 | +0.044 | -12.5 | 3266 | -0.037 | -0.044 | -18.5 | +0.21 / +0.53 | PASS |
|  | V04 window end 15:00->14:00 (P6) | 189 | +0.145 | +0.049 | -13.0 | 4117 | -0.035 | -0.041 | -25.3 | +1.55 / +0.15 | PASS |
|  | V05 window start 09:50->10:15 (P6/P7) | 208 | +0.121 | +0.041 | -13.4 | 4590 | -0.024 | -0.030 | -25.3 | +0.31 / +1.65 | PASS |
|  | V06 refire on, cooldown 6 (P8) | 206 | +0.111 | +0.029 | -13.4 | 4715 | -0.029 | -0.035 | -25.3 | -1.00 / +1.17 | PASS |
|  | V07 heat <= -35 (P9) | 95 | -0.072 | -0.132 | -10.7 | 2619 | -0.055 | -0.061 | -20.1 | -1.37 / +0.01 | FAIL — replay avg R -0.072 < parent +0.117; replay w/o best day -0.132 vs +0.036; 2y avg R -0.055 < parent -0.031; 2y w/o best day -0.061 vs -0.037 |
|  | V09 buyPressure < -0.20 (P10) | 141 | +0.108 | +0.039 | -9.3 | 3458 | -0.022 | -0.028 | -21.7 | -0.79 / +1.58 | PASS |
|  | V10 RSI(5) > 85 (P11) | 166 | +0.136 | +0.047 | -12.7 | 3692 | -0.027 | -0.033 | -21.4 | -0.17 / +0.97 | PASS |
|  | V11 RSI(5) <= 97 (P11 cap) | 164 | +0.138 | +0.047 | -11.0 | 3803 | -0.052 | -0.058 | -21.6 | -0.20 / -1.42 | FAIL — 2y avg R -0.052 < parent -0.031; 2y w/o best day -0.058 vs -0.037 |
|  | V12 gap < -0.5% (P12) | 156 | +0.126 | +0.018 | -8.6 | 2469 | -0.026 | -0.036 | -27.2 | -0.35 / +1.23 | PASS |
|  | V13 gap < -1.0% (P12) | 118 | +0.161 | +0.016 | -7.5 | 1424 | -0.040 | -0.060 | -27.2 | -0.32 / +1.04 | FAIL — 2y w/o best day -0.060 vs -0.037 |
|  | V14 latch -2R -> -4R (P16, tool) | 216 | +0.108 | +0.030 | -14.4 | 5127 | -0.036 | -0.042 | -25.3 | -0.24 / -1.66 | PASS |
|  | V15 1R 0.25 -> 0.30 ATR (P20) | 215 | +0.067 | -0.015 | -14.5 | 4786 | -0.037 | -0.042 | -23.4 | -1.74 / -0.89 | FAIL — replay avg R +0.067 < parent +0.117; replay w/o best day -0.015 vs +0.036 |
| WB2 | V16 cost/R <= 0.15 (P20/intake) | 145 | +0.122 | +0.034 | -10.3 | 3570 | -0.022 | -0.028 | -15.9 | -0.58 / +1.49 | PASS |
|  | V17 stop 1.0 -> 1.25R (P23) | 217 | +0.063 | -0.020 | -18.9 | 4908 | -0.033 | -0.038 | -31.2 | -1.55 / -0.43 | FAIL — replay avg R +0.063 < parent +0.117; replay w/o best day -0.020 vs +0.036; replay worst day -18.9 vs -13.4R; 2y worst day -31.2 vs -25.3R |
|  | V18 target 1.0 -> 0.8R (P24) | 205 | +0.102 | +0.020 | -13.4 | 4764 | -0.041 | -0.045 | -24.8 | -0.73 / -1.93 | FAIL — replay avg R +0.102 < parent +0.117 |
|  | V19 BE stop after +0.5R (P23 move) | 205 | +0.092 | +0.007 | -12.3 | 4679 | -0.043 | -0.049 | -24.0 | -0.65 / -1.52 | FAIL — replay avg R +0.092 < parent +0.117; replay w/o best day +0.007 vs +0.036; 2y avg R -0.043 < parent -0.031 |
|  | V20 max hold 90 min (P26) | 194 | +0.129 | +0.064 | -7.6 | 4666 | -0.045 | -0.050 | -16.8 | +0.07 / -1.09 | FAIL — 2y avg R -0.045 < parent -0.031 |
|  | V21 max hold 120 min (P26) | 198 | +0.143 | +0.066 | -9.1 | 4659 | -0.041 | -0.046 | -21.0 | +0.41 / -1.00 | PASS |
|  | V22 flat 15:55 -> 15:00 (P26) | 205 | +0.142 | +0.056 | -11.4 | 4632 | -0.032 | -0.037 | -20.5 | +0.63 / -0.01 | PASS |
| WB1 | V23 gate: skip SPY > +0.30% since 09:50 (new) | 156 | +0.184 | +0.088 | -12.5 | 3670 | -0.007 | -0.014 | -25.3 | +0.30 / +2.50 | PASS |
|  | V24 gate: skip SPY above 09:30-09:50 high (new) | 132 | +0.180 | +0.059 | -12.5 | 2848 | -0.003 | -0.012 | -26.2 | -0.01 / +1.97 | PASS |
|  | S1 skip SPY > +0.20% since 09:50 | 141 | +0.200 | +0.095 | -12.5 | 3227 | -0.008 | -0.016 | -25.3 | +0.25 / +1.98 | PASS |
|  | S2 skip SPY > +0.45% since 09:50 | 176 | +0.164 | +0.077 | -12.5 | 4145 | -0.022 | -0.028 | -25.3 | +0.44 / +1.53 | PASS |
|  | C1 SPY gate + cost/R<=0.15 | 108 | +0.174 | +0.062 | -10.3 | 2812 | +0.001 | -0.007 | -15.9 | -0.27 / +2.26 | PASS |
|  | C2 C1 + start 10:15 | 107 | +0.167 | +0.051 | -10.3 | 2740 | +0.011 | +0.003 | -15.9 | -0.32 / +2.62 | PASS |
|  | C3 C1 + RSI(5)>85 | 78 | +0.195 | +0.058 | -5.1 | 2183 | -0.001 | -0.009 | -13.3 | -0.41 / +1.79 | PASS |
|  | C4 C1 + bp<-0.20 | 77 | +0.133 | +0.054 | -7.6 | 2091 | +0.015 | +0.010 | -14.1 | -0.63 / +2.22 | PASS |
|  | C5 C2 + price>=$10 | 107 | +0.167 | +0.051 | -10.3 | 2738 | +0.011 | +0.003 | -15.9 | -0.32 / +2.61 | PASS |
|  | C6 C1 + end 14:00 | 99 | +0.205 | +0.085 | -10.3 | 2488 | -0.008 | -0.016 | -15.9 | -0.20 / +1.82 | PASS |
|  | C7 C2 + end 14:00 | 98 | +0.197 | +0.074 | -10.3 | 2412 | +0.001 | -0.007 | -15.9 | -0.24 / +2.12 | PASS |
|  | C8 spyrng gate + cost/R<=0.15 + start 10:15 | 96 | +0.160 | +0.025 | -10.3 | 2133 | +0.023 | +0.013 | -15.9 | -0.41 / +2.45 | PASS |
|  | C9 C2 + flat 15:00 (no live knob) | 107 | +0.194 | +0.075 | -8.2 | 2740 | +0.001 | -0.007 | -14.6 | -0.16 / +1.94 | PASS |
|  | C10 SPY gate + start 10:15 | 153 | +0.182 | +0.083 | -12.5 | 3581 | +0.002 | -0.005 | -25.3 | +0.23 / +2.93 | PASS |
| WB3 | D1 C2 with SPY gate 0.20 | 100 | +0.191 | +0.072 | -10.3 | 2435 | +0.017 | +0.009 | -15.9 | -0.24 / +2.51 | PASS |
|  | D2 C2 with cost/R<=0.10 | 86 | +0.148 | -0.000 | -10.5 | 2168 | +0.009 | -0.000 | -13.0 | -0.56 / +2.17 | FAIL — replay w/o best day -0.000 vs +0.036 |
|  | D3 C2 + RSI(5)>85 | 78 | +0.195 | +0.058 | -5.1 | 2129 | +0.016 | +0.007 | -13.3 | -0.41 / +2.31 | PASS |

| config | TRAIN avg R (n) | VALID avg R (n) | FWD avg R (n) |
|---|---|---|---|
| PARENT | -0.047 (2341) | -0.035 (2030) | +0.129 (262) |
| V01 ADV >= $150M (P2) | -0.049 (1729) | -0.068 (1553) | +0.032 (150) |
| V02 price >= $10 (P3) | -0.046 (2313) | -0.038 (2016) | +0.138 (259) |
| V03 window end 15:00->13:00 (P6) | -0.042 (1666) | -0.057 (1408) | +0.155 (192) |
| V04 window end 15:00->14:00 (P6) | -0.043 (2065) | -0.050 (1812) | +0.154 (240) |
| V05 window start 09:50->10:15 (P6/P7) | -0.038 (2308) | -0.030 (2016) | +0.139 (266) |
| V06 refire on, cooldown 6 (P8) | -0.045 (2383) | -0.031 (2066) | +0.131 (266) |
| V07 heat <= -35 (P9) | -0.049 (1363) | -0.076 (1128) | +0.065 (128) |
| V09 buyPressure < -0.20 (P10) | -0.026 (1776) | -0.041 (1488) | +0.159 (194) |
| V10 RSI(5) > 85 (P11) | -0.017 (1893) | -0.045 (1613) | +0.024 (186) |
| V11 RSI(5) <= 97 (P11 cap) | -0.065 (1918) | -0.056 (1684) | +0.107 (201) |
| V12 gap < -0.5% (P12) | -0.052 (1109) | -0.026 (1174) | +0.135 (186) |
| V13 gap < -1.0% (P12) | -0.083 (546) | -0.053 (756) | +0.226 (122) |
| V14 latch -2R -> -4R (P16, tool) | -0.042 (2563) | -0.048 (2284) | +0.108 (280) |
| V15 1R 0.25 -> 0.30 ATR (P20) | -0.041 (2417) | -0.042 (2122) | +0.052 (247) |
| V16 cost/R <= 0.15 (P20/intake) | -0.024 (1757) | -0.039 (1614) | +0.141 (199) |
| V17 stop 1.0 -> 1.25R (P23) | -0.043 (2475) | -0.040 (2167) | +0.122 (266) |
| V18 target 1.0 -> 0.8R (P24) | -0.049 (2400) | -0.046 (2098) | +0.080 (266) |
| V19 BE stop after +0.5R (P23 move) | -0.046 (2366) | -0.060 (2053) | +0.119 (260) |
| V20 max hold 90 min (P26) | -0.056 (2328) | -0.052 (2072) | +0.109 (266) |
| V21 max hold 120 min (P26) | -0.048 (2339) | -0.056 (2055) | +0.133 (265) |
| V22 flat 15:55 -> 15:00 (P26) | -0.037 (2339) | -0.049 (2031) | +0.156 (262) |
| V23 gate: skip SPY > +0.30% since 09:50 (new) | -0.045 (1814) | +0.015 (1636) | +0.152 (220) |
| V24 gate: skip SPY above 09:30-09:50 high (new) | -0.042 (1302) | +0.012 (1389) | +0.181 (157) |
| S1 skip SPY > +0.20% since 09:50 | -0.048 (1575) | +0.013 (1463) | +0.167 (189) |
| S2 skip SPY > +0.45% since 09:50 | -0.049 (2075) | -0.014 (1814) | +0.142 (256) |
| C1 SPY gate + cost/R<=0.15 | -0.023 (1351) | +0.005 (1300) | +0.172 (161) |
| C2 C1 + start 10:15 | -0.015 (1317) | +0.013 (1262) | +0.210 (161) |
| C3 C1 + RSI(5)>85 | +0.013 (1081) | -0.020 (999) | +0.037 (103) |
| C4 C1 + bp<-0.20 | +0.002 (1013) | +0.003 (954) | +0.213 (124) |
| C5 C2 + price>=$10 | -0.015 (1316) | +0.012 (1261) | +0.210 (161) |
| C6 C1 + end 14:00 | -0.026 (1181) | -0.017 (1157) | +0.199 (150) |
| C7 C2 + end 14:00 | -0.020 (1143) | -0.009 (1117) | +0.238 (152) |
| C8 spyrng gate + cost/R<=0.15 + start 10:15 | -0.002 (951) | +0.021 (1063) | +0.233 (119) |
| C9 C2 + flat 15:00 (no live knob) | -0.013 (1317) | -0.018 (1262) | +0.268 (161) |
| C10 SPY gate + start 10:15 | -0.037 (1772) | +0.024 (1597) | +0.171 (212) |
| D1 C2 with SPY gate 0.20 | -0.011 (1147) | +0.021 (1146) | +0.221 (142) |
| D2 C2 with cost/R<=0.10 | -0.016 (1048) | +0.009 (996) | +0.217 (124) |
| D3 C2 + RSI(5)>85 | +0.016 (1033) | -0.007 (970) | +0.194 (126) |

Notes on the table: V01 (ADV) cannot be replayed (replay = names that passed $95M live), so its replay row equals the parent.
V14 (latch −4R) is a backtest-only tool part. V22 / C9 (flat 15:00) have no per-setup live knob (the runner flattens at
15:55 for all setups; `Signal.exit_by` is not acted on live), so they are not shippable. Passing parts NOT shipped: V02 / V06 /
V14 (gain ~0), V03 / V04 (2-year VALID worse), V09 / V10 / V12 (one test only or thin FWD), V21 / V22 (2-year no better), V24
(range gate: fewer trades for the same gain as V23), C3 / D3 (RSI > 85: FWD +0.037 in C3), C4 (replay +0.133), C8 (replay w/o
best day +0.025), C10 (2-year worst day unchanged −25.3R).
FAIL: V01 ADV $150M, V07 heat <= −35, V11 RSI(5) <= 97, V13 gap < −1%, V15 1R 0.30 ATR, V17 stop 1.25R, V18 target 0.8R,
V19 breakeven after +0.5R, V20 max hold 90 min, D2 cost/R <= 0.10 (replay w/o best day 0.000).

## Shape (2-year; SPY day type open->close > +0.25% up / < −0.25% down; extras.csv)
| config | test | avg win | avg loss | median hold (min) | stop share | target share | up-day avg R (n) | flat | down |
|---|---|---|---|---|---|---|---|---|---|
| PARENT | replay | +0.797 | −0.769 | 124 | 22% | 41% | | | |
| PARENT | 2y | +0.778 | −0.848 | 106 | 32% | 34% | −0.286 (1,579) | +0.052 (1,601) | +0.154 (1,453) |
| WB1 (V23) | 2y | +0.783 | −0.860 | 103 | 32% | 36% | −0.302 (904) | +0.033 (1,347) | +0.144 (1,419) |
| WB2 (V16) | 2y | +0.778 | −0.833 | 106 | 32% | 34% | −0.258 (1,219) | +0.061 (1,222) | +0.144 (1,129) |
| WB3 (D1) | replay | +0.821 | −0.794 | 122 | 21% | 45% | | | |
| WB3 (D1) | 2y | +0.774 | −0.827 | 105 | 31% | 35% | −0.225 (516) | +0.013 (870) | +0.141 (1,049) |

The gate works by cutting up-day exposure (1,579 → 516 trades), not by improving the trades it keeps on up days much; flat
days give back a little (+0.052 → +0.013).

## Pending config change — "ready to deploy after close" (NOT applied; built during market hours)
The main session applies this after 16:05 ET (`TZ=America/New_York date`), effective session 2026-11-17. One copy only:
**WB3** (it contains WB1's gate and WB2's filter; running them side by side would be near-twins). The parent stays in Primary,
unchanged (Workbench rule 1). Destination: **Testing D** (`config/account_testingd.yaml`) — a testing account, not Primary
(rule 5 / TEAM-6 note: a passing copy never goes to Primary); Testing D has no RW-family / RW3-RW5 gap-down pop short (its
NM-RWR1 gap-down short trades only when SPY is UP, the opposite state of WB3's gate), it already runs `context: [spy_fo]`
setups, and its account cost filter `max_stop_cost_r: 0.15` matches WB3's own clause. If another Workbench job has already
claimed the FIRST slot in Testing D tonight, put WB3 right after it (the main session decides the order between Workbench copies).
1. Module: copy `research/workbench/RW5-heat30-flowsell-rsi5pop-gapdn-short-FD/modules/RW5-heat30-flowsell-rsi5pop-gapdn-short-FD-WB3.py`
   to `research/bdi/fullday/RW5-heat30-flowsell-rsi5pop-gapdn-short-FD-WB3.py`.
2. `config/account_testingd.yaml`, under `strategies:` add
   ```yaml
   RW5-heat30-flowsell-rsi5pop-gapdn-short-FD-WB3:
     # Workbench copy of RW5-heat30-flowsell-rsi5pop-gapdn-short-FD (Primary), Mechanic 2026-11-16: + skip when SPY is up
     # > +0.20% since 09:50 + stop cost <= 0.15R + window from 10:15; research/workbench/RW5-.../RESULTS.md. From session 2026-11-17.
     enabled: true
     type: lab
     module: research/bdi/fullday/RW5-heat30-flowsell-rsi5pop-gapdn-short-FD-WB3.py
     min_adv: 95000000
     window: [1015, 1500]
     context: [spy_fo]
     scale_out_r: null
     tags: [workbench, "parent:RW5-heat30-flowsell-rsi5pop-gapdn-short-FD"]
   ```
   (refire stays off, as the parent in Primary) and put `RW5-heat30-flowsell-rsi5pop-gapdn-short-FD-WB3` FIRST in
   `live.setup_order` (rule 5).
3. `config/setup_names.yaml`: `RW5-heat30-flowsell-rsi5pop-gapdn-short-FD-WB3: {name: "Gap-Down Pop Fade (all day) — WB3: SPY-since-09:50 gate + stop cost <= 15% of 1R + start 10:15", side: short, what: "10:15-15:00: a gapped-down stock with bearish heat and net selling pops to RSI(5) > 80; short the pop unless SPY is up more than 0.20% since 09:50 or the stop cost is over 15% of 1R; target / stop 1R (0.25 ATR), flat 15:55."}`
4. `research/ledger.jsonl`: id `2026-11-16-wb-rw5-wb3`, effective 2026-11-17, title "Workbench copy
   RW5-heat30-flowsell-rsi5pop-gapdn-short-FD-WB3 added to Testing D, first in setup_order (Mechanic pass)", patch
   `{"strategies.RW5-heat30-flowsell-rsi5pop-gapdn-short-FD-WB3 (testingd)": [null, "added, enabled"], "live.setup_order (testingd)": ["...", "WB3 first"]}`,
   evidence this file, approved_by "owner rule research/workbench/RULES.md 5"; then `python -m mcf.research.ledger check`.
5. Smoke test (module needs the `spy_fo` context column; without it the mask fires nothing — fail safe), `python -m
   mcf.report.assignments` (docs/live/assignments.json in the same commit), `pytest -q`, commit, push after 16:05 ET (setup-freeze).
Note: Testing D runs its own book (no Primary −2R latch / 30-lot cap as modelled here), so live numbers will not match these
tables one for one.
